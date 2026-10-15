"""Cinematic dark-product environment for the Mango Loco can.

Adds the CINEMATIC collection on top of the standard asset: a machined dark
plinth on a reflective resin floor, a ribbed industrial wall, emerald and teal
neon practicals, volumetric haze with a green god-ray spotlight, a dramatic
light rig, depth-of-field cameras and a subtle compositor bloom. The classic
STUDIO rig is hidden, never deleted, so the scene stays reversible.

One Blender unit is one metre. The product origin is its bottom centre at z=0.
This module only adds objects and configures render defaults; it never clears
a scene or saves a .blend file.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import bpy
from mathutils import Vector


def _section(cfg, name):
    if isinstance(cfg, Mapping):
        return cfg.get(name, {})
    return getattr(cfg, name, {})


def _collection(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _link_object(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _material(name, color, roughness=0.5, metallic=0.0, anisotropy=0.0, noise_rough=None):
    """Dark environment material with optional large-scale roughness break-up."""
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Anisotropic IOR Level" in bsdf.inputs:
        bsdf.inputs["Anisotropic IOR Level"].default_value = anisotropy
    if noise_rough:
        nodes, links = material.node_tree.nodes, material.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-560, -220)
        noise.inputs["Scale"].default_value = 2.6
        noise.inputs["Detail"].default_value = 3.0
        rough = nodes.new("ShaderNodeMapRange")
        rough.location = (-300, -220)
        rough.inputs["To Min"].default_value = noise_rough[0]
        rough.inputs["To Max"].default_value = noise_rough[1]
        links.new(noise.outputs["Fac"], rough.inputs["Value"])
        links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    return material


def _emission(name, color, strength):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1.0)
    emit.inputs["Strength"].default_value = strength
    out.location = (200, 0)
    material.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    material["practical"] = "emissive neon for the cinematic set"
    return material


def _aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _area_light(collection, name, location, target, power, size_x, size_y, color, shape="RECTANGLE"):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = power
    data.shape = shape
    data.size = size_x
    if shape == "RECTANGLE":
        data.size_y = size_y
    data.color = color
    data.use_shadow = True
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    _aim(obj, target)
    obj["set_control"] = "CINEMATIC"
    obj["power_watts"] = power
    return obj


def _camera(collection, name, location, target, lens, focus_distance, fstop, resolution):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36.0
    data.clip_start = 0.001
    data.clip_end = 100.0
    data.dof.use_dof = True
    data.dof.focus_distance = focus_distance
    data.dof.aperture_fstop = fstop
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    _aim(obj, target)
    obj["set_control"] = "CINEMATIC"
    obj["target"] = tuple(target)
    obj["recommended_resolution"] = resolution
    return obj


def _ribbed_wall(cine, wall_mat):
    """Flat dark panel with vertical corrugations for parallax and rim catch."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.05, 0.75))
    panel = bpy.context.object
    panel.name = "CINE_Back_Wall"
    _link_object(panel, cine)
    panel.dimensions = (3.4, 0.04, 1.70)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    panel.data.materials.append(wall_mat)
    panel["set_control"] = "CINEMATIC"

    ribs_verts, ribs_faces = [], []
    count, spacing, width, depth = 26, 0.13, 0.020, 0.030
    for index in range(count):
        x = (index - (count - 1) / 2) * spacing
        y0, y1 = 1.028, 1.028 - depth
        z0, z1 = -0.06, 1.55
        base = len(ribs_verts)
        ribs_verts.extend([(x - width / 2, y0, z0), (x + width / 2, y0, z0),
                           (x + width / 2, y1, z0), (x - width / 2, y1, z0),
                           (x - width / 2, y0, z1), (x + width / 2, y0, z1),
                           (x + width / 2, y1, z1), (x - width / 2, y1, z1)])
        ribs_faces.extend([(base + 0, base + 1, base + 5, base + 4),
                           (base + 1, base + 2, base + 6, base + 5),
                           (base + 2, base + 3, base + 7, base + 6),
                           (base + 3, base + 0, base + 4, base + 7),
                           (base + 4, base + 5, base + 6, base + 7)])
    mesh = bpy.data.meshes.new("CINE_RibsMesh")
    mesh.from_pydata(ribs_verts, [], ribs_faces)
    mesh.update()
    ribs = bpy.data.objects.new("CINE_Wall_Ribs", mesh)
    cine.objects.link(ribs)
    mesh.materials.append(wall_mat)
    ribs["set_control"] = "CINEMATIC"
    return panel, ribs


def _neon_tube(cine, name, location, length, radius, axis, emission_mat):
    rotation = (0, math.pi / 2, 0) if axis == "X" else (0, 0, 0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=length,
                                        location=location, rotation=rotation)
    tube = bpy.context.object
    tube.name = name
    _link_object(tube, cine)
    tube.data.materials.append(emission_mat)
    half = length / 2
    offsets = ((0, 0, half), (0, 0, -half)) if axis == "Z" else ((half, 0, 0), (-half, 0, 0))
    for cap_offset in offsets:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=radius,
                                             location=Vector(location) + Vector(cap_offset))
        cap = bpy.context.object
        cap.name = name + "_Cap"
        _link_object(cap, cine)
        cap.data.materials.append(emission_mat)
    tube["set_control"] = "CINEMATIC"
    return tube


def _plinth(cine, plinth_mat):
    for name, r, depth, z, bevel in (
        ("CINE_Plinth_Top", 0.052, 0.012, -0.006, 0.0012),
        ("CINE_Plinth_Foot", 0.058, 0.008, -0.016, 0.0010),
    ):
        bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=r, depth=depth, location=(0, 0, z))
        obj = bpy.context.object
        obj.name = name
        _link_object(obj, cine)
        obj.data.materials.append(plinth_mat)
        bevel_mod = obj.modifiers.new("Soft machined edge", "BEVEL")
        bevel_mod.width = bevel
        bevel_mod.segments = 4
        bevel_mod.limit_method = "ANGLE"
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
        obj["set_control"] = "CINEMATIC"


def _world(scene, haze_density):
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("CINEMATIC_World")
        scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    background = nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.010, 0.011, 0.013, 1.0)
        background.inputs["Strength"].default_value = 1.0
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.location = (-240, -200)
    volume.inputs["Color"].default_value = (0.50, 0.58, 0.55, 1.0)
    volume.inputs["Density"].default_value = haze_density
    volume.inputs["Anisotropy"].default_value = 0.30
    output = next(node for node in nodes if node.type == "OUTPUT_WORLD")
    links.new(volume.outputs["Volume"], output.inputs["Volume"])


def _gpu(scene):
    """Best available Cycles backend; harmless fallback to CPU everywhere."""
    preferences = bpy.context.preferences.addons.get("cycles")
    if preferences is None:
        scene.cycles.device = "CPU"
        return "CPU"
    try:
        preferences.preferences.refresh_devices()
    except Exception:
        pass
    for backend in ("OPTIX", "CUDA"):
        try:
            preferences.preferences.compute_device_type = backend
            preferences.preferences.refresh_devices()
        except Exception:
            continue
        devices = [d for d in preferences.preferences.devices if d.type == backend]
        if devices:
            for device in preferences.preferences.devices:
                device.use = device.type == backend
            scene.cycles.device = "GPU"
            scene.cycles.denoiser = "OPTIX" if backend == "OPTIX" else "OPENIMAGEDENOISE"
            return backend
    scene.cycles.device = "CPU"
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    return "CPU"


def _compositor(scene, cfg):
    """Subtle fog-glow bloom via the compositor. Blender 5.x exposes the
    compositor as a node group on the scene; older versions use scene.node_tree."""
    cine = _section(cfg, "CINEMATIC")
    threshold = float(cine.get("glare_threshold", 1.15))
    if hasattr(scene, "compositing_node_group"):
        group = bpy.data.node_groups.get("Cinematic_Compositor") or \
            bpy.data.node_groups.new("Cinematic_Compositor", "CompositorNodeTree")
        nodes, links = group.nodes, group.links
        nodes.clear()
        layers = nodes.new("CompositorNodeRLayers")
        layers.location = (-400, 0)
        glare = nodes.new("CompositorNodeGlare")
        glare.location = (-120, 0)
        if "Type" in glare.inputs:  # 5.x socket-driven glare
            glare.inputs["Type"].default_value = "Fog Glow"
            glare.inputs["Quality"].default_value = "High"
            glare.inputs["Threshold"].default_value = threshold
            glare.inputs["Size"].default_value = float(cine.get("glare_size", 0.55))
            if "Strength" in glare.inputs:
                glare.inputs["Strength"].default_value = float(cine.get("glare_strength", 0.35))
        else:  # 4.x property-driven glare
            glare.glare_type = "FOG_GLOW"
            glare.quality = "HIGH"
            glare.threshold = threshold
            glare.size = 7
            glare.mix = -0.55
        output = nodes.new("NodeGroupOutput")
        output.location = (220, 0)
        if not any(item.in_out == "OUTPUT" for item in group.interface.items_tree):
            group.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        links.new(layers.outputs["Image"], glare.inputs["Image"])
        links.new(glare.outputs["Image"], output.inputs["Image"])
        scene.compositing_node_group = group
    else:  # Blender 4.x scene node tree
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        layers = tree.nodes.new("CompositorNodeRLayers")
        layers.location = (-400, 0)
        glare = tree.nodes.new("CompositorNodeGlare")
        glare.location = (-120, 0)
        glare.glare_type = "FOG_GLOW"
        glare.quality = "HIGH"
        glare.threshold = threshold
        glare.size = 7
        glare.mix = -0.55
        composite = tree.nodes.new("CompositorNodeComposite")
        composite.location = (220, 0)
        tree.links.new(layers.outputs["Image"], glare.inputs["Image"])
        tree.links.new(glare.outputs["Image"], composite.inputs["Image"])


def build(cfg, materials, parts):
    """Build the cinematic set; returns {cine_*: camera} for build_project."""
    scene = bpy.context.scene
    can_cfg = _section(cfg, "CAN")
    cine_cfg = _section(cfg, "CINEMATIC")
    height = float(can_cfg.get("height", 0.15723))

    # Retire the classic ivory studio without deleting it: the scene stays
    # reversible and the STUDIO collection keeps its documented controls.
    studio = bpy.data.collections.get("STUDIO")
    if studio:
        for obj in studio.objects:
            obj.hide_render = True
            obj.hide_set(True)

    cine = _collection("CINEMATIC")
    cameras_collection = _collection("CAMERAS")

    floor_mat = _material("CINE_Floor_Resin", (0.012, 0.013, 0.014), 0.30, noise_rough=(0.22, 0.42))
    wall_mat = _material("CINE_Wall_DarkSteel", (0.020, 0.022, 0.025), 0.62)
    plinth_mat = _material("CINE_Plinth_MachinedDark", (0.045, 0.048, 0.052), 0.36, metallic=0.9, anisotropy=0.35)
    emerald = tuple(cine_cfg.get("neon_emerald", (0.18, 1.0, 0.45)))
    teal = tuple(cine_cfg.get("neon_teal", (0.12, 0.75, 1.0)))
    neon_emerald = _emission("CINE_Neon_Emerald", emerald, 24.0)
    neon_teal = _emission("CINE_Neon_Teal", teal, 9.0)

    # Room: reflective resin floor plus the corrugated back wall.
    bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=3.0, depth=0.006, location=(0, 0, -0.023))
    floor = bpy.context.object
    floor.name = "CINE_Floor"
    _link_object(floor, cine)
    floor.data.materials.append(floor_mat)
    floor["set_control"] = "CINEMATIC"
    _ribbed_wall(cine, wall_mat)

    # Product support: a low machined plinth whose top sits exactly at z=0.
    _plinth(cine, plinth_mat)

    # Neon practicals. The vertical emerald tube is the hero backlight; the
    # teal tube and floor strip add depth without cluttering the frame.
    _neon_tube(cine, "CINE_Neon_Tube_Emerald", (-0.38, 0.58, 0.32), 0.55, 0.0045, "Z", neon_emerald)
    _neon_tube(cine, "CINE_Neon_Tube_Teal", (0.36, 0.55, 0.06), 0.72, 0.0045, "X", neon_teal)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.02, 0.30, -0.0185))
    strip = bpy.context.object
    strip.name = "CINE_Neon_Floor_Strip"
    _link_object(strip, cine)
    strip.dimensions = (0.34, 0.012, 0.003)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    strip.data.materials.append(_emission("CINE_Neon_Floor_Mat", emerald, 10.0))
    strip["set_control"] = "CINEMATIC"

    for name, location, color, power in (
        ("CINE_Neon_Glow_A", (-0.38, 0.58, 0.32), emerald, 1.4),
        ("CINE_Neon_Glow_B", (0.36, 0.55, 0.06), teal, 0.7),
    ):
        data = bpy.data.lights.new(name, type="POINT")
        data.energy = power
        data.color = color
        data.shadow_soft_size = 0.03
        obj = bpy.data.objects.new(name, data)
        cine.objects.link(obj)
        obj.location = location
        obj["set_control"] = "CINEMATIC"

    # Dramatic product rig: hard warm key, split emerald/teal rim, dim cool
    # fill, top kick for the lid, and a hazy green god-ray behind the can.
    focus = (0.0, 0.0, height * 0.55)
    _area_light(cine, "CINE_Key_Softbox", (-0.26, -0.30, 0.40), focus,
                float(cine_cfg.get("key_power", 20.0)), 0.30, 0.55, (1.0, 0.965, 0.90))
    _area_light(cine, "CINE_Rim_Green", (-0.14, 0.28, 0.20), focus,
                float(cine_cfg.get("rim_green_power", 14.0)), 0.06, 0.52, (0.35, 1.0, 0.55))
    _area_light(cine, "CINE_Rim_Teal", (0.22, 0.24, 0.14), focus,
                float(cine_cfg.get("rim_teal_power", 5.5)), 0.05, 0.30, (0.40, 0.85, 1.0))
    _area_light(cine, "CINE_Fill_Cool", (0.36, -0.30, 0.14), focus,
                float(cine_cfg.get("fill_power", 0.80)), 0.34, 0.46, (0.72, 0.80, 0.92))
    _area_light(cine, "CINE_Top_Kick", (0.06, -0.20, 0.40), (0.0, 0.0, height * 1.03),
                float(cine_cfg.get("top_kick_power", 2.5)), 0.14, 0.14, (1.0, 1.0, 1.0))

    spot_data = bpy.data.lights.new("CINE_Godray_Spot", type="SPOT")
    spot_data.energy = float(cine_cfg.get("godray_power", 38.0))
    spot_data.color = (0.55, 1.0, 0.62)
    spot_data.spot_size = 0.12
    spot_data.spot_blend = 0.6
    spot_data.shadow_soft_size = 0.03
    spot = bpy.data.objects.new("CINE_Godray_Spot", spot_data)
    cine.objects.link(spot)
    spot.location = (0.34, 0.20, 1.30)
    _aim(spot, (-0.10, 0.35, -0.02))
    spot["set_control"] = "CINEMATIC"

    _world(scene, float(cine_cfg.get("haze_density", 0.010)))

    cameras = {
        "cine_hero": _camera(cameras_collection, "CAM_Cine_Hero", (0.185, -0.545, 0.093),
                             (0.004, 0.0, 0.086), 88.0, 0.545, 3.2, (1440, 1800)),
        "cine_macro": _camera(cameras_collection, "CAM_Cine_Macro", (0.098, -0.152, 0.182),
                              (0.0, -0.010, 0.149), 85.0, 0.178, 3.2, (1440, 1800)),
        "cine_wide": _camera(cameras_collection, "CAM_Cine_Wide", (0.48, -0.72, 0.165),
                             (0.0, 0.04, 0.090), 46.0, 0.900, 4.5, (1920, 1080)),
        "cine_top": _camera(cameras_collection, "CAM_Cine_Top", (0.045, -0.085, 0.345),
                            (0.0, -0.005, 0.158), 85.0, 0.206, 6.3, (1440, 1440)),
    }

    scene.render.engine = "CYCLES"
    backend = _gpu(scene)
    scene.cycles.samples = int(cine_cfg.get("samples", 224))
    scene.cycles.preview_samples = int(cine_cfg.get("preview_samples", 64))
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.010
    scene.cycles.max_bounces = 10
    scene.cycles.transmission_bounces = 8
    scene.cycles.volume_bounces = 2
    scene.cycles.sample_clamp_indirect = 10.0
    try:
        scene.cycles.use_light_tree = True
    except Exception:
        pass
    for attr in ("filter_size", "filter_width"):  # name differs across Blender versions
        if hasattr(scene.render, attr):
            setattr(scene.render, attr, 1.3)
            break
    scene.render.resolution_x, scene.render.resolution_y = 1440, 1800
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = cine_cfg.get("look", "AgX - Punchy")
    except TypeError:
        scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = float(cine_cfg.get("exposure", 0.0))
    _compositor(scene, cfg)
    scene["cinematic_backend"] = backend
    scene["cinematic_note"] = ("Dark industrial set with neon practicals and haze; "
                               "classic STUDIO rig hidden under the STUDIO collection.")
    return cameras
