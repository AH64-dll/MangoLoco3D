"""Procedural, editable Monster Mango Loco can geometry.

All dimensions are metres.  Geometry is built in its final local position under
CAN_Rig; this module never clears a scene, saves a file, or creates simulation.
"""
import math
import bpy
import bmesh
from mathutils import Vector


def _collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _link(obj, collection):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def _mesh_obj(name, verts, faces, collection):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def _lathe(name, profile, segments, collection, label_range=None, materials=None,
           label_segments=None, flat_z=()):
    """Revolve a closed r,z cross-section; profile starts and ends on axis."""
    if len(profile) > 2 and profile[0] == profile[-1]:
        profile = profile[:-1]
    verts, faces = [], []
    for r, z in profile:
        for i in range(segments):
            a = 2 * math.pi * i / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(len(profile)):
        jn = (j + 1) % len(profile)
        for i in range(segments):
            a, b = j * segments + i, j * segments + (i + 1) % segments
            c, d = jn * segments + (i + 1) % segments, jn * segments + i
            faces.append((a, b, c, d))
    obj = _mesh_obj(name, verts, faces, collection)
    if materials:
        for mat in materials:
            if mat and mat.name not in obj.data.materials:
                obj.data.materials.append(mat)
        if label_range and len(obj.data.materials) > 1:
            lo, hi = label_range
            for poly_index, poly in enumerate(obj.data.polygons):
                profile_segment = poly_index // segments
                zmid = sum(obj.data.vertices[k].co.z for k in poly.vertices) / len(poly.vertices)
                # Callers select only exterior profile spans for printed ink.
                eligible = (label_segments is None and 8 <= profile_segment <= 15)
                if label_segments is not None:
                    eligible = profile_segment in label_segments
                if eligible and lo <= zmid <= hi:
                    poly.material_index = 1
    # Cylindrical UVs: u=.5 at front (-Y), with the only seam at +Y.
    uv = obj.data.uv_layers.new(name="CanWrap")
    for poly in obj.data.polygons:
        loop_uvs = []
        for li in poly.loop_indices:
            vi = obj.data.loops[li].vertex_index
            v = obj.data.vertices[vi].co
            ang = math.atan2(v.y, v.x)
            u = ((ang - math.pi / 2) / (2 * math.pi)) % 1.0
            vv = v.z
            if label_range:
                vv = (v.z - label_range[0]) / (label_range[1] - label_range[0])
                # Repeat only around the can. Neck vertices above the label
                # must retain its cyan top edge, not wrap to the bottom art.
                vv = max(.0003,min(.9997,vv))
            uv.data[li].uv = (u, vv)
            loop_uvs.append((li, u, vv))
        if loop_uvs and max(item[1] for item in loop_uvs) - min(item[1] for item in loop_uvs) > .5:
            # Keep each seam-crossing quad locally continuous across U=1.
            for li, u, vv in loop_uvs:
                if u < .5:
                    uv.data[li].uv = (u + 1.0, vv)
    # Weld any coincident profile points and give the closed shell consistent normals.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-8,edges=bm.edges)
    bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    for p in obj.data.polygons:
        p.use_smooth = not any(abs(p.center.z - z) < 1e-7 for z in flat_z)
    return obj


def _cube(name, loc, dims, collection, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    _link(obj, collection)
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Rolled edge radii", "BEVEL")
        mod.width = bevel
        mod.segments = 4
        mod.affect = 'EDGES'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def _rounded_prism(name, loc, width, length, depth, corner, collection, steps=10):
    """Extruded rounded outline whose corner radius survives thin extrusion."""
    hx, hy = width / 2, length / 2
    r = min(corner, hx, hy)
    corners = ((hx-r, hy-r, 0), (-hx+r, hy-r, 90),
               (-hx+r, -hy+r, 180), (hx-r, -hy+r, 270))
    outline = []
    for cx, cy, start_deg in corners:
        for k in range(steps + 1):
            a = math.radians(start_deg + 90 * k / steps)
            outline.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    n = len(outline)
    verts = [(x, y, z) for z in (-depth/2, depth/2) for x, y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces.extend((i, (i+1) % n, (i+1) % n + n, i+n) for i in range(n))
    obj = _mesh_obj(name, verts, faces, collection)
    obj.location = loc
    return obj


def _score_curve(name, points, z, collection, bevel_depth):
    curve = bpy.data.curves.new(name + "Curve", 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, (x, y) in zip(spline.points, points):
        point.co = (x, y, z, 1)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    return obj


def _cylinder(name, loc, radius, depth, collection, vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    _link(obj, collection)
    for p in obj.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return obj


def _torus(name, loc, major, minor, collection, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                    major_segments=128, minor_segments=12,
                                    location=loc, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    _link(obj, collection)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def _apply_boolean(target, cutter, operation='DIFFERENCE'):
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    cutter.select_set(False)
    mod = target.modifiers.new("Baked manufactured aperture", "BOOLEAN")
    mod.operation = operation
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _assign(obj, material):
    if material:
        obj.data.materials.append(material)


def _parent(obj, root):
    obj.parent = root
    return obj


def build_can(cfg, materials):
    """Build the modular can and return the supervisor/physics interface."""
    can = cfg.get("CAN", cfg)
    radius = float(can.get("radius", .03325))
    height = float(can.get("height", .168))
    zscale = height / .168
    Z = lambda value: value * zscale
    wall = float(can.get("wall", .00012))
    neck = float(can.get("neck_radius", .028))
    seg = int(can.get("segments", 256))
    label_bottom = float(can.get("label_bottom", .004))
    label_top = float(can.get("label_top", .163))
    geom = _collection("CAN_GEOMETRY")
    details = _collection("CAN_DETAILS")
    sim = _collection("SIMULATION")
    source_collection = _collection("CAN_SOURCE")

    root = bpy.data.objects.new("CAN_Rig", None)
    geom.objects.link(root)
    root.empty_display_type = 'CIRCLE'
    root.empty_display_size = radius * 1.25
    root.location = (0, 0, 0)
    root["opening"] = 0.0
    root["fill_level"] = float(can.get("fill_level", .82))
    root.id_properties_ui("opening").update(min=0.0, max=1.0, description="0 closed, 1 opened")
    root.id_properties_ui("fill_level").update(min=0.0, max=1.0, description="Static liquid height fraction")

    # One closed profile folds over the double seam and into the interior.  The
    # bottom climbs into a shallow dome; the shoulder and neck are distinct.
    ri = radius - max(wall, .00018)
    profile = [
        (0.0, Z(.0050)), (.0200, Z(.0046)), (.0275, Z(.0020)), (.0294, Z(.0010)),
        (.0306, Z(.0012)), (.0313, Z(.0021)), (.0316, Z(.0032)), (.0320, Z(.0040)),
        (radius * .985, Z(.0055)), (radius, Z(.0080)), (radius, Z(.1450)),
        (radius * .996, Z(.1500)), (radius * .978, Z(.1530)), (radius * .925, Z(.1560)),
        (neck * 1.035, Z(.1590)), (neck, Z(.1610)), (neck, Z(.1642)),
        (neck * 1.025, Z(.1650)), (neck * 1.055, Z(.1656)),
        (neck * 1.065, Z(.1662)), (neck * 1.035, Z(.1668)), (neck * .985, Z(.1668)),
        (neck * .955, Z(.1662)), (neck * .955, Z(.1645)), (neck * .970, Z(.1615)),
        (neck * 1.012, Z(.1598)), (radius * .900, Z(.1568)), (radius * .955, Z(.1535)),
        (ri, Z(.1495)), (ri, Z(.0080)), (.0308, Z(.0045)), (.0297, Z(.0031)),
        (.0270, Z(.0037)), (.0190, Z(.0060)), (0.0, Z(.0061)), (0.0, Z(.0050))
    ]
    profile = can.get('profile_points',profile)

    # Keep the complete editable shell as a hidden source. Render geometry is
    # split at the barrel's lower z=.008 m station into independently selectable
    # closed top body and concave bottom dome. Both share a flat annular mating
    # face and global cylindrical UV convention; there is no volume overlap.
    profile = list(profile)
    if len(profile) < 30:
        raise ValueError("CAN profile_points must contain at least 30 ordered r,z samples for body/bottom split")
    outer_station = next((i for i, (r, z) in enumerate(profile)
                          if i < 15 and r >= radius * .999 and abs(z - Z(.0080)) < 1e-7), None)
    inner_station = next((i for i, (r, z) in enumerate(profile)
                          if i > 15 and r < radius * .999 and abs(z - Z(.0080)) < 1e-7), None)
    if outer_station is None or inner_station is None:
        raise ValueError("CAN profile_points must include outer and inner z=.008 m split stations")
    body_profile = profile[outer_station:inner_station + 1]
    bottom_profile = profile[:outer_station + 1] + profile[inner_station:]
    flat_station = Z(.0080)
    body = _lathe("CAN_Body", body_profile, seg, geom, (label_bottom, label_top),
                  [materials.get("aluminum"), materials.get("label")],
                  label_segments=range(0, min(7, len(body_profile) - 1)), flat_z=(flat_station,))
    bottom = _lathe("CAN_Bottom_Dome", bottom_profile, seg, geom, (label_bottom, label_top),
                    [materials.get("aluminum"), materials.get("label")],
                    label_segments=(7, 8), flat_z=(flat_station,))
    source = _lathe("CAN_Clean_Source", profile, seg, source_collection,
                    (label_bottom, label_top),
                    [materials.get("aluminum"), materials.get("label")])
    source.hide_render = True
    source.hide_set(True)
    source["purpose"] = "Preserved complete hollow shell source; hidden while modular render parts are active"
    body["wall_thickness_nominal_m"] = wall
    body["label_uv"] = "U wraps from +Y seam; U=.5 at front -Y; V=0..1 between label_bottom and label_top"

    # Top lid disc; the rounded-rectangle cut is a genuine through aperture.
    lid_top = Z(.16645)
    lid_thickness = Z(float(can.get('lid_thickness',.00084)))
    lid = _cylinder("CAN_Lid", (0, 0, lid_top - lid_thickness/2), neck * 1.045, lid_thickness, geom, 192)
    _assign(lid, materials.get("aluminum"))
    aperture_y = float(can.get('aperture_y',-.0105))
    aperture_size = can.get('aperture_size',(.0225,.0125))
    cutter = _cube("_aperture_tool", (0, aperture_y, lid_top), (*aperture_size, Z(.006)), geom, .0022)
    _apply_boolean(lid, cutter)
    for p in lid.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    # Raised perimeter bead and shallow concentric lid embossing.
    rim = _torus("CAN_Rolled_Rim", (0, 0, Z(.16615)), neck * 1.037, can.get('rim_tube',.00072) * zscale, details)
    _assign(rim, materials.get("aluminum"))
    emboss = _torus("CAN_Lid_Emboss", (0, .008, lid_top + Z(.00008)), .0068, .00016 * zscale, details)
    _assign(emboss, materials.get("aluminum"))
    emboss_inner = _torus("CAN_Lid_Emboss_Inner", (0, .008, lid_top + Z(.00008)), .00625, .00010 * zscale, details)
    _assign(emboss_inner, materials.get("dark_metal"))

    # Hinged scored panel closes the hole at rest; opening drives it down into
    # the cavity through the baked aperture, with its hinge at the +Y edge.
    hinge_y = aperture_y + aperture_size[1]/2-.0001
    panel = _rounded_prism("CAN_Scored_Panel", (0, aperture_y, lid_top + Z(.00020)),
                           aperture_size[0]-.0008, aperture_size[1]-.0009, Z(.00055), .0021, details, 12)
    _assign(panel, materials.get("aluminum"))
    pivot = Vector((0, hinge_y, lid_top + Z(.0002)))
    old_location = panel.location.copy()
    for v in panel.data.vertices:
        v.co += old_location - pivot
    panel.location = pivot
    panel["hinge_axis"] = "X"
    d = panel.driver_add("rotation_euler", 0).driver
    d.type = 'SCRIPTED'
    var = d.variables.new(); var.name = "opening"; var.type = 'SINGLE_PROP'
    var.targets[0].id = root; var.targets[0].data_path = '["opening"]'
    d.expression = 'opening * ' + str(can.get('panel_rotation',.92))
    score_points = [(-.0109, -.0042), (-.0109, -.0135), (-.0098, -.0158),
                    (-.0078, -.0167), (.0078, -.0167), (.0098, -.0158),
                    (.0109, -.0135), (.0109, -.0042)]
    score = _score_curve("CAN_Panel_Score", score_points, lid_top + Z(.000035), details, .00011)
    _assign(score, materials.get("dark_metal"))

    # Separate stamped pull tab, with two real punched holes and a raised nose.
    tab_size=can.get('tab_size',(.0134,.027,.00075))
    tab = _rounded_prism("CAN_Pull_Tab", (0, -.002, Z(.16755)),
                         tab_size[0], tab_size[1], Z(tab_size[2]), .0062, details, 14)
    _assign(tab, materials.get("tab"))
    for yy, rr in ((.0065, .0041), (.0010, .0017)):
        punch = _cylinder("_tab_punch", (0, yy, Z(.16755)), rr, Z(.004), details, 48)
        _apply_boolean(tab, punch)
    # A small stamped reinforcing bridge over the central spine.
    bridge = _cube("CAN_Tab_Raised_Spine", (0, -.003, Z(.16803)), (.0020, .008, Z(.00035)), details, .00015)
    _assign(bridge, materials.get("tab"))
    tab_pivot = Vector((0, .001, Z(.16755)))
    old_location = tab.location.copy()
    for v in tab.data.vertices:
        v.co += old_location - tab_pivot
    tab.location = tab_pivot
    dt = tab.driver_add("rotation_euler", 0).driver
    dt.type = 'SCRIPTED'
    var = dt.variables.new(); var.name = "opening"; var.type = 'SINGLE_PROP'
    var.targets[0].id = root; var.targets[0].data_path = '["opening"]'
    dt.expression = 'opening * ' + str(can.get('tab_rotation',.62))

    rivet = _cylinder("CAN_Tab_Rivet", (0, .001, Z(.16718)), .00165, Z(.00075), details, 64)
    _assign(rivet, materials.get("dark_metal"))
    rivet_bead = _torus("CAN_Rivet_Bead", (0, .001, Z(.16758)), .00165, .00022 * zscale, details)
    _assign(rivet_bead, materials.get("aluminum"))

    # Independent thick collision proxy made from the same real container wall
    # silhouette. It stays separate from the printable/render body and is hidden
    # from product renders; the open top permits the liquid setup to use it.
    collision_profile = list(profile)
    clearance = .0015
    # Offset the complete inner return by the chosen collision thickness while
    # preserving the outer silhouette and the true open neck.
    for i in range(22, len(collision_profile) - 1):
        r, z = collision_profile[i]
        collision_profile[i] = (max(.0002, r - clearance), z)
    coll = _lathe("SIM_Can_Collider", collision_profile, max(96, seg // 2), sim)
    coll.hide_render = True
    coll.hide_set(True)
    coll.display_type = 'WIRE'
    coll["purpose"] = "Hidden thick-wall collision proxy; rebuild at 1.5 mm clearance for fluid baking if required"
    coll["nominal_collision_wall_m"] = .0015

    for obj in (body, bottom, source, lid, rim, emboss, emboss_inner, panel, score, tab, rivet, rivet_bead):
        _parent(obj, root)
    bridge.parent = tab
    bridge.matrix_parent_inverse = tab.matrix_world.inverted()
    coll.parent = root
    # Seat the bottom foot exactly at the rig origin while keeping CAN_Rig at
    # its floor-level base. All direct children share this small manufacturing
    # datum correction; bridge remains a child of tab and follows automatically.
    for obj in root.children:
        obj.location.z -= Z(.001)
    root["profile_base_offset_m"] = Z(.001)
    return {"root": root, "body": body, "bottom": bottom, "clean_source": source,
            "lid": lid, "tab": tab, "panel": panel, "collider": coll,
            "rim": rim, "rivet": rivet}

