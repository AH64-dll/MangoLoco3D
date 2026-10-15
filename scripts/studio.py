"""Reusable, physically based product studio for the Mango Loco can.

One Blender unit is one metre. The product origin is its bottom centre at z=0.
This module only adds studio objects and configures render defaults; it never
clears a scene or saves a .blend file.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import bpy
from mathutils import Vector


def _section(cfg, name):
    """Read a section from either config.py, a mapping, or a section mapping."""
    if isinstance(cfg, Mapping):
        return cfg.get(name, {})
    return getattr(cfg, name, {})


def _value(cfg, section, key, default):
    values = _section(cfg, section)
    if isinstance(values, Mapping):
        return values.get(key, default)
    return getattr(values, key, default)


def _collection(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _link_object(obj, collection):
    # Objects created by bpy.ops are linked to the active collection. Move
    # them into the studio collection so scene organization stays predictable.
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _material(name, color, roughness=0.55, metallic=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
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
    obj["studio_control"] = True
    obj["power_watts"] = power
    return obj


def _make_camera(collection, name, location, target, lens, resolution_x, resolution_y, ortho_scale=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36.0
    data.clip_start = 0.001
    data.clip_end = 100.0
    if ortho_scale is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    _aim(obj, target)
    obj["studio_control"] = True
    obj["target"] = tuple(target)
    obj["recommended_resolution"] = (resolution_x, resolution_y)
    return obj


def _make_cyclorama(collection, material):
    """Surround cameras with a seamless radial floor-to-wall cove."""
    floor_z=-.020
    radius=.65
    cove=.16
    profile=[(radius,floor_z)]
    for step in range(1,25):
        angle=-math.pi/2+math.pi/2*step/24
        profile.append((radius+cove*math.cos(angle),floor_z+cove+cove*math.sin(angle)))
    profile.append((radius+cove,1.34))
    segments=160
    vertices=[(0,0,floor_z)]
    for r,z in profile:
        vertices.extend((r*math.cos(math.tau*i/segments),r*math.sin(math.tau*i/segments),z) for i in range(segments))
    faces=[(0,1+i,1+(i+1)%segments) for i in range(segments)]
    for row in range(len(profile)-1):
        for i in range(segments):
            a=1+row*segments+i
            b=1+row*segments+(i+1)%segments
            c=1+(row+1)*segments+(i+1)%segments
            d=1+(row+1)*segments+i
            faces.append((a,d,c,b))
    mesh=bpy.data.meshes.new('STUDIO_Cyclorama_Mesh')
    mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new('STUDIO_Ivory_Cyclorama',mesh)
    collection.objects.link(obj);mesh.materials.append(material)
    for poly in mesh.polygons:poly.use_smooth=True
    obj['studio_control']=True
    obj['cove_radius_m']=cove
    obj['background']='360 degree cove for front, side and pour cameras'
    return obj


def build_studio(cfg) -> dict:
    """Build camera and lighting rigs; return front/three-quarter/side/top/hero cameras.

    ``cfg`` may be the project's config module, a mapping with CAN and RENDER
    sections, or the CAN section itself. The returned values are camera
    objects, ready to assign to ``scene.camera``. Call this once per scene.
    """
    scene = bpy.context.scene
    can_cfg = _section(cfg, "CAN")
    if not can_cfg and isinstance(cfg, Mapping) and "radius" in cfg:
        can_cfg = cfg
    radius = can_cfg.get("radius", 0.033)
    height = can_cfg.get("height", 0.15723)
    render_cfg = _section(cfg, "RENDER")
    if not isinstance(render_cfg, Mapping):
        render_cfg = {}
    preview = render_cfg.get("preview_size", (720, 900))
    final = render_cfg.get("final_size", (1440, 1800))
    preview_samples = render_cfg.get("preview_samples", 32)
    final_samples = render_cfg.get("final_samples", 160)

    studio = _collection("STUDIO")
    cameras_collection = _collection("CAMERAS")

    ivory = _material("STUDIO_Warm_Ivory", (0.72, 0.675, 0.58), roughness=0.66)
    pedestal_mat = _material("STUDIO_Pedestal_Burnt_Orange", (0.16, 0.045, 0.018), roughness=0.54)

    # A two-step, softly bevelled plinth puts its top exactly at the product
    # origin. The lower disc and ground finish the edge with a subtle shadow.
    for name, r, depth, z, bevel in (
        ("STUDIO_Pedestal_Top", radius * 1.57, 0.014, -0.007, 0.0012),
        ("STUDIO_Pedestal_Foot", radius * 1.70, 0.006, -0.017, 0.0010),
    ):
        bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=r, depth=depth, location=(0, 0, z))
        obj = bpy.context.object
        obj.name = name
        _link_object(obj, studio)
        obj.data.materials.append(pedestal_mat)
        bevel_mod = obj.modifiers.new("Soft machined edge", "BEVEL")
        bevel_mod.width = bevel
        bevel_mod.segments = 4
        bevel_mod.limit_method = "ANGLE"
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
        obj["studio_control"] = True

    _make_cyclorama(studio, ivory)

    # Broad emitters paint long, soft aluminum highlights. A warm key and
    # neutral fills keep the orange/teal label saturated and the metal legible.
    focus = (0.0, 0.0, height * 0.54)
    _area_light(studio, "STUDIO_Key_Softbox", (-0.19, -0.24, 0.30), focus,
                1.10, 0.22, 0.38, (1.0, 0.96, 0.90))
    _area_light(studio, "STUDIO_Fill_Softbox", (0.20, -0.15, 0.20), focus,
                0.42, 0.17, 0.30, (0.90, 0.96, 1.0))
    _area_light(studio, "STUDIO_Rim_Strip", (0.13, 0.15, 0.25), focus,
                0.66, 0.085, 0.34, (1.0, 0.76, 0.51))
    _area_light(studio, "STUDIO_Front_Card", (-0.02, -0.30, 0.13), focus,
                0.18, 0.13, 0.23, (1.0, 0.96, 0.88))

    # Use a gentle world contribution as the ambient fill; the visible sweep
    # and area sources provide the background gradient and object reflections.
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("STUDIO_World")
        scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.42, 0.39, 0.34, 1.0)
        background.inputs["Strength"].default_value = 0.28

    # Portrait framing leaves a little breathing room while keeping the can
    # large. Hero is a mild three-quarter view with a visible lid and side wall.
    portrait_x, portrait_y = int(preview[0]), int(preview[1])
    cameras = {
        "front": _make_camera(cameras_collection, "CAM_Front", (0.0, -0.48, height * 0.57),
                              (0.0, 0.0, height * 0.51), 76.0, portrait_x, portrait_y),
        "three_quarter": _make_camera(cameras_collection, "CAM_Three_Quarter",
                                      (0.19, -0.47, height * 0.70),
                                      (0.0, 0.0, height * 0.51), 78.0, portrait_x, portrait_y),
        "side": _make_camera(cameras_collection, "CAM_Side", (0.46, 0.0, height * 0.57),
                             (0.0, 0.0, height * 0.51), 76.0, portrait_x, portrait_y),
        # Close, near-orthographic lid framing makes the pull tab and aperture
        # readable without forcing depth of field onto the detailed mechanism.
        "top": _make_camera(cameras_collection, "CAM_Top_Detail", (0.0, -0.012, 0.43),
                            (0.0, 0.0, height), 70.0, int(preview[0]), int(preview[0]),
                            ortho_scale=radius * 2.45),
        "hero": _make_camera(cameras_collection, "CAM_Hero", (0.16, -0.46, height * 0.74),
                             (0.0, 0.0, height * 0.52), 82.0, int(final[0]), int(final[1])),
    }

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.preview_samples = int(preview_samples)
    scene.cycles.samples = int(final_samples)
    scene.cycles.use_denoising = True
    scene.render.resolution_x = portrait_x
    scene.render.resolution_y = portrait_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    return cameras
