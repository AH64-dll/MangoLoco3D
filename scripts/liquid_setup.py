"""Editable still liquid and a reproducible Mantaflow pour setup.

All dimensions are metres.  This module only adds objects/modifiers; it never
clears or saves the scene and deliberately does not start an expensive bake.
The cache is portable relative to the saved physics .blend file.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import bpy
import bmesh


def _section(cfg, name):
    if isinstance(cfg, Mapping):
        return cfg.get(name, {})
    return getattr(cfg, name, {})


def _collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _link(obj, col):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def _mesh_object(name, verts, faces, col):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def _revolved_shell(name, profile, segments, col):
    """Make a closed surface of revolution from a closed radial cross-section."""
    verts, faces = [], []
    for radius, z in profile:
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    for row in range(len(profile)):
        next_row = (row + 1) % len(profile)
        for i in range(segments):
            a = row * segments + i
            b = row * segments + (i + 1) % segments
            c = next_row * segments + (i + 1) % segments
            d = next_row * segments + i
            faces.append((a, b, c, d))
    obj = _mesh_object(name, verts, faces, col)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-8, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def _closed_fill_mesh(name, radius, bottom, top, col, segments=96):
    """A closed cylindrical fluid volume with flat top and bottom faces."""
    verts = [(0.0, 0.0, bottom)]
    for z in (bottom, top):
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    top_center = len(verts)
    verts.append((0.0, 0.0, top))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        # Bottom fan, vertical wall, top fan; winding points outward.
        faces.append((0, 1 + j, 1 + i))
        faces.append((1 + i, 1 + j, 1 + segments + j, 1 + segments + i))
        faces.append((top_center, 1 + segments + i, 1 + segments + j))
    return _mesh_object(name, verts, faces, col)


def _bevelled_aperture_cut(lid, aperture_y, can_scale, size=(.0225,.0125)):
    """Cut the same 22.5 x 12.5 mm opening used by geometry.build_can."""
    # Build the cutter with operators so its rounded rectangle matches the real lid.
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, aperture_y, lid.location.z))
    cutter = bpy.context.object
    cutter.name = "_SIM_Aperture_Cut"
    _link(cutter, _collection("SIMULATION"))
    cutter.dimensions = (*size, 0.006 * can_scale)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = cutter.modifiers.new("Rounded aperture corners", "BEVEL")
    bevel.width = 0.0022
    bevel.segments = 4
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    lid.select_set(True)
    cutter.select_set(False)
    bpy.context.view_layer.objects.active = lid
    boolean = lid.modifiers.new("Real drinking aperture", "BOOLEAN")
    boolean.operation = 'DIFFERENCE'
    boolean.solver = 'EXACT'
    boolean.object = cutter
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _effector(obj, name, distance=0.25):
    mod = obj.modifiers.new(name, 'FLUID')
    mod.fluid_type = 'EFFECTOR'
    settings = mod.effector_settings
    settings.surface_distance = distance
    settings.use_effector = True
    settings.subframes = 3
    return mod


def _flow(obj):
    mod = obj.modifiers.new("Liquid | initial can contents", 'FLUID')
    mod.fluid_type = 'FLOW'
    settings = mod.flow_settings
    settings.flow_type = 'LIQUID'
    settings.flow_behavior = 'GEOMETRY'
    settings.flow_source = 'MESH'
    settings.surface_distance = 0.0
    settings.use_inflow = True
    settings.use_initial_velocity = False
    obj.hide_render = True
    obj.display_type = 'WIRE'
    obj["purpose"] = "One-shot initial liquid volume; render-hidden and disabled after settle frames"
    return settings


def _parent_to_root(obj, root):
    if root is not None:
        obj.parent = root
    return obj


def build_static(cfg, materials, parts):
    """Build a separately editable still-liquid volume driven by CAN_Rig.fill_level."""
    can = _section(cfg, "CAN")
    if not can and isinstance(cfg, Mapping) and "radius" in cfg:
        can = cfg
    radius = float(can.get("radius", 0.033))
    height = float(can.get("height", 0.15723))
    fill = float(can.get("fill_level", 0.82))
    root = parts.get("root")
    col = _collection("LIQUID_STATIC")
    inner_radius = radius - 0.0020
    bottom = 0.006
    max_top = min(height - 0.019, height * 0.91)
    base_top = bottom + 0.0005
    obj = _closed_fill_mesh("LIQ_Static_Fill", inner_radius, bottom, base_top, col)
    obj.data.materials.append(materials["liquid"])
    _parent_to_root(obj, root)
    # The upper ring and cap move as one shape, leaving the bottom unchanged.
    basis = obj.shape_key_add(name="Basis")
    fill_shape = obj.shape_key_add(name="Fill level 0 to 1")
    segments = 96
    for index in range(1 + segments, 1 + 2 * segments + 1):
        fill_shape.data[index].co.z = max_top
    if root is not None:
        driver = fill_shape.driver_add("value").driver
        driver.type = 'SCRIPTED'
        variable = driver.variables.new()
        variable.name = "fill_level"
        variable.type = 'SINGLE_PROP'
        variable.targets[0].id = root
        variable.targets[0].data_path = '["fill_level"]'
        driver.expression = "fill_level"
    else:
        fill_shape.value = fill
    obj["fill_height_m"] = "Driven by CAN_Rig['fill_level'] from the bottom up"
    obj["separate_from_can_geometry"] = True
    return obj


def build_dynamic(cfg, materials, parts):
    """Create a native Mantaflow liquid domain, initial source, and collision rig.

    Returns ``(domain, resources)``.  The scene is configured for a 64-frame
    modular liquid bake, but no data or mesh bake is started here.
    """
    scene = bpy.context.scene
    can = _section(cfg, "CAN")
    sim = _section(cfg, "SIM")
    if not can and isinstance(cfg, Mapping) and "radius" in cfg:
        can = cfg
    radius = float(can.get("radius", 0.033))
    height = float(can.get("height", 0.15723))
    fill_level = float(can.get("fill_level", 0.82))
    resolution = int(sim.get("resolution", 96))
    resolution = max(96, resolution)
    frame_end = int(sim.get("frames", 64))
    fps = int(sim.get("fps", 24))
    cache_directory = str(sim.get("cache", "//../cache/liquid/pour_verified_v4"))
    root = parts["root"]
    col = _collection("SIMULATION")
    scale = height / 0.168  # geometry.build_can's shared height multiplier
    neck = float(can.get("neck_radius", 0.028))
    bottom_z = 0.002 * scale
    top_z = 0.1645 * scale
    inner_bottom = 0.0300
    inner_r = radius - 0.003
    outer_r = radius + 0.0030

    # Closed thick shell: a 6 mm solver wall, inner wall, and bottom.
    # Its neck ends in a real annular lip; the separate lid insert is perforated.
    shell_profile = [
        (outer_r, bottom_z), (outer_r, 0.1450 * scale),
        (radius * .996 + .0030, .1500 * scale),
        (radius * .978 + .0030, .1530 * scale),
        (neck * 1.035 + .0030, .1590 * scale),
        (neck + .0030, .1610 * scale), (neck + .0030, top_z),
        (neck - .0030, top_z), (neck - .0030, .1610 * scale),
        (neck * 1.012, .1598 * scale), (radius * .900, .1568 * scale),
        (inner_r, .1535 * scale), (inner_r, .0080 * scale),
        (inner_bottom, .0065 * scale), (0.0, .0065 * scale),
        (0.0, bottom_z), (inner_bottom, bottom_z),
    ]
    shell = _revolved_shell("SIM_Can_Wall_Proxy", shell_profile, 128, col)
    shell["wall_proxy_thickness_m"] = outer_r - inner_r
    shell["boundary_note"] = "Thick closed bottom and walls; unobstructed at top until aperture lid insert"
    _parent_to_root(shell, root)
    _effector(shell, "Liquid | can wall collision", sim.get('effector_distance',.25))
    shell.hide_render = True
    shell.display_type = 'WIRE'

    lid_depth = sim.get('lid_collision_thickness',.004) * scale
    lid_z = top_z - lid_depth * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=neck * 1.045,
                                        depth=lid_depth, location=(0.0, 0.0, lid_z))
    lid_proxy = bpy.context.object
    lid_proxy.name = "SIM_Can_Lid_Proxy"
    _link(lid_proxy, col)
    _bevelled_aperture_cut(lid_proxy, can.get('aperture_y',-.0105), scale, can.get('aperture_size',(.0225,.0125)))
    _parent_to_root(lid_proxy, root)
    _effector(lid_proxy, "Liquid | perforated lid collision", sim.get('effector_distance',.25))
    lid_proxy.hide_render = True
    lid_proxy.display_type = 'WIRE'
    lid_proxy["aperture_matches_can"] = "22.5 x 12.5 mm rounded rectangle centred at local y=-10.5 mm"

    # A low-resolution glass receiver both collects liquid and remains visible
    # in the physics preview so the stream has a clear destination.
    bowl_y = float(sim.get('receiver_y',-.213))
    bowl_profile = [
        (0.0, .0010), (.0260, .0010), (.0340, .0030), (.0380, .0120),
        (.0400, .0260), (.0380, .0270), (.0355, .0140), (.0305, .0070),
        (0.0, .0060),
    ]
    bowl = _revolved_shell("SIM_Receiver_Bowl_Proxy", bowl_profile, 96, col)
    bowl.location.y = bowl_y
    glass = bpy.data.materials.new("SIM | clear receiver glass")
    glass.diffuse_color = (0.48, 0.72, 0.78, 0.24)
    glass.use_nodes = True
    glass_bsdf = glass.node_tree.nodes.get("Principled BSDF")
    if glass_bsdf:
        glass_bsdf.inputs["Base Color"].default_value = (0.48, 0.72, 0.78, 0.24)
        glass_bsdf.inputs["Roughness"].default_value = 0.12
        glass_bsdf.inputs["IOR"].default_value = 1.45
        if "Transmission Weight" in glass_bsdf.inputs:
            glass_bsdf.inputs["Transmission Weight"].default_value = 0.82
        elif "Transmission" in glass_bsdf.inputs:
            glass_bsdf.inputs["Transmission"].default_value = 0.82
    bowl.data.materials.append(glass)
    bowl.hide_render = False
    bowl.display_type = 'WIRE'
    _effector(bowl, "Liquid | receiver collision", 0.5)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.07, -0.004))
    ground = bpy.context.object
    ground.name = "SIM_Ground_Collision"
    _link(ground, col)
    ground.dimensions = (0.60, 0.60, 0.008)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _effector(ground, "Liquid | ground collision", 0.25)
    ground.hide_render = True

    # The source geometry is an honest initial liquid volume inside the can.
    usable_height = max(0.05, min(height - 0.020, height * 0.86))
    source_bottom = 0.008 * scale
    source_top = source_bottom + usable_height * fill_level
    source = _closed_fill_mesh("SIM_Initial_Juice_Volume", inner_r - sim.get('source_clearance',.005),
                               source_bottom, source_top, col, segments=64)
    _parent_to_root(source, root)
    flow_settings = _flow(source)
    source["initial_fill_level"] = fill_level
    source["initial_liquid_height_m"] = source_top - source_bottom
    flow_settings.keyframe_insert(data_path="use_inflow", frame=1, group="One-shot source")
    flow_settings.use_inflow = False
    flow_settings.keyframe_insert(data_path="use_inflow", frame=9, group="One-shot source")

    # Domain surrounds the full can arc, stream path, and receiving bowl.  Its
    # longest side at 96 cells gives approximately 3.3 mm cells; the aperture
    # spans about 3.7 x 6.7 cells, a deliberate low-cost first bake.
    domain_min = (-0.070, -0.255, -0.010)
    domain_max = (0.070, 0.065, 0.190)
    dims = tuple(domain_max[i] - domain_min[i] for i in range(3))
    center = tuple((domain_max[i] + domain_min[i]) * 0.5 for i in range(3))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    domain = bpy.context.object
    domain.name = "SIM_Liquid_Domain"
    _link(domain, col)
    domain.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = domain.modifiers.new("Mantaflow | liquid domain", 'FLUID')
    modifier.fluid_type = 'DOMAIN'
    settings = modifier.domain_settings
    settings.domain_type = 'LIQUID'
    settings.cache_type = 'MODULAR'
    settings.cache_directory = cache_directory
    settings.cache_frame_start = 1
    settings.cache_frame_end = frame_end
    settings.cache_data_format = 'OPENVDB'
    settings.cache_mesh_format = 'BOBJECT'
    settings.resolution_max = resolution
    settings.use_adaptive_domain = False
    settings.use_mesh = True
    settings.mesh_scale = sim.get('mesh_scale',2)
    settings.mesh_particle_radius = 1.0
    settings.time_scale = sim.get('time_scale',.5)
    settings.cfl_condition = 2.0
    settings.use_viscosity = False
    settings.use_diffusion = True
    settings.viscosity_base = sim.get('viscosity_base',4.)
    settings.viscosity_exponent = sim.get('viscosity_exponent',6)
    settings.surface_tension = sim.get('surface_tension',0.)
    settings.flip_ratio = 0.97
    settings.particle_radius = 1.0
    settings.use_collision_border_front = True
    settings.use_collision_border_back = True
    settings.use_collision_border_left = True
    settings.use_collision_border_right = True
    settings.use_collision_border_top = True
    settings.use_collision_border_bottom = True
    domain.data.materials.append(materials["liquid"])
    domain["simulation_status"] = "Configured only; data and mesh cache have not been baked or visually reviewed"
    domain["voxel_estimate_m"] = max(dims) / resolution
    domain["cache_contract"] = cache_directory
    domain.display_type = 'WIRE'
    static = bpy.data.objects.get("LIQ_Static_Fill")
    if static:
        static.hide_render = True
        static.hide_set(True)
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.render.fps = fps

    return domain, {
        "source": source,
        "wall_proxy": shell,
        "lid_proxy": lid_proxy,
        "receiver_proxy": bowl,
        "ground": ground,
        "root": root,
        "cache_directory": cache_directory,
        "resolution": resolution,
        "voxel_size_m_estimate": max(dims) / resolution,
    }
