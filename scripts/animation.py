"""Keyframe helpers for the initial low-cost liquid-pour demonstration."""
from __future__ import annotations

from collections.abc import Mapping
import math

import bpy


def _section(cfg, name):
    if isinstance(cfg, Mapping):
        return cfg.get(name, {})
    return getattr(cfg, name, {})


def build_pour_animation(cfg, parts, resources=None):
    """Animate the can opening and tipping forward 110 degrees toward -Y.

    The animation gives the source eight settle frames, tips over 24 frames,
    then holds through the configured 64-frame preview. Translation lifts the
    spout above the receiver instead of inserting the can's lid into the bowl.
    """
    can = _section(cfg, "CAN")
    sim = _section(cfg, "SIM")
    if not can and isinstance(cfg, Mapping) and "radius" in cfg:
        can = cfg
    root = parts["root"]
    radius = float(can.get("radius", 0.033))
    height = float(can.get("height", 0.15723))
    fps = int(sim.get("fps", 24))
    frame_end = int(sim.get("frames", 64))
    settle_end = min(8, frame_end)
    tilt_start = settle_end + 1
    tilt_end = min(tilt_start + 24, frame_end)
    angle = math.radians(110.0)
    lift = float(sim.get('pour_lift',.030))

    root.rotation_mode = 'XYZ'

    def pose(frame, theta):
        # Keep the lower front edge at y=-r. Raise the root only as needed to
        # keep the can's complete cylindrical silhouette at or above ground.
        root.location = (0.0, -radius + radius * math.cos(theta),
                         radius * math.sin(theta) + max(0.0, -height * math.cos(theta))
                         + lift * theta / angle)
        root.rotation_euler = (theta, 0.0, 0.0)
        root.keyframe_insert(data_path="location", frame=frame, group="Can pour")
        root.keyframe_insert(data_path="rotation_euler", frame=frame, group="Can pour")

    for frame in range(1,frame_end+1):
        t=max(0.,min(1.,(frame-tilt_start)/max(1,tilt_end-tilt_start)))
        pose(frame,angle*t*t*(3.-2.*t))
    for layer in root.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:point.interpolation='LINEAR'
    # The genuine geometry.build_can panel and tab already read this control.
    for frame, value in ((1, 1.0), (frame_end, 1.0)):
        root["opening"] = value
        root.keyframe_insert(data_path='["opening"]', frame=frame, group="Can pour")

    # Keep liquid source emission fixed to the first eight frames. Its flow
    # modifier also has matching use_inflow keys from liquid_setup.build_dynamic.
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.render.fps = fps
    root["pour_tilt_degrees"] = 110.0
    root["pour_lift_m"] = lift
    root["pour_direction"] = "Forward toward -Y; receiver centered at y="+str(sim.get('receiver_y',-.213))+" m"
    root["pour_timing_frames"] = {"settle_end": settle_end,
                                  "tilt_start": tilt_start,
                                  "tilt_end": tilt_end,
                                  "hold_end": frame_end}
    return {
        "root": root,
        "settle_end": settle_end,
        "tilt_start": tilt_start,
        "tilt_end": tilt_end,
        "hold_end": frame_end,
        "tilt_degrees": 110.0,
    }


def build_turntable(root, frames=120, fps=24):
    """Optional five-second clean turntable; use on a copy of the studio rig."""
    root.rotation_mode='XYZ'
    root.rotation_euler=(0,0,0)
    root.keyframe_insert(data_path='rotation_euler',frame=1)
    root.rotation_euler.z=math.tau
    root.keyframe_insert(data_path='rotation_euler',frame=frames+1)
    action=root.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:point.interpolation='LINEAR'
    bpy.context.scene.frame_end=frames
    bpy.context.scene.render.fps=fps
    bpy.context.scene.frame_set(1)
