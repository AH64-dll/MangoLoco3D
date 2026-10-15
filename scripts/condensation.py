"""Procedural surface condensation for the Mango Loco can.

Builds ``CAN_Condensation``: a single editable mesh of water beads placed on
the can's real outer profile (barrel, shoulder, neck), a scatter on the lid,
optional drip streaks hanging from large beads, and optional beads on the
studio plinth. Everything is a closed, manifold shell so the standard asset
validator stays green.

One Blender unit is one metre. Beads are parented to CAN_Rig with the same
manufacturing datum correction as the other can parts. Regenerate by rerunning
this module through scripts/build_project.py; size, count and seed come from
the CINEMATIC section of config.py.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import random

import bpy
from mathutils import Matrix, Vector


def _section(cfg, name):
    if isinstance(cfg, Mapping):
        return cfg.get(name, {})
    return getattr(cfg, name, {})


def _sphere_template(segments=12, rings=8):
    """Unit UV sphere; returns (verts, faces) with closed pole fans."""
    verts, faces = [], []
    for i in range(1, rings):
        phi = math.pi * i / rings
        z, r = math.cos(phi), math.sin(phi)
        for j in range(segments):
            a = math.tau * j / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    north, south = len(verts), len(verts) + 1
    verts.append((0.0, 0.0, 1.0))
    verts.append((0.0, 0.0, -1.0))
    row = lambda i: i * segments
    for j in range(segments):
        faces.append((north, row(0) + (j + 1) % segments, row(0) + j))
    for i in range(rings - 2):
        for j in range(segments):
            a = row(i) + j
            b = row(i) + (j + 1) % segments
            c = row(i + 1) + (j + 1) % segments
            d = row(i + 1) + j
            faces.append((a, b, c, d))
    last = row(rings - 2)
    for j in range(segments):
        faces.append((south, last + j, last + (j + 1) % segments))
    return verts, faces


class _Surface:
    """Outer can surface from the real profile stations, in body local units."""

    def __init__(self, can):
        radius = float(can.get("radius", 0.033))
        height = float(can.get("height", 0.15723))
        neck = float(can.get("neck_radius", 0.028))
        self.zscale = height / 0.168
        # Profile stations from geometry.py, already scaled; values are in the
        # same local frame the CAN_Body mesh uses before the datum shift.
        raw = [
            (.0080, radius), (.1450, radius), (.1500, radius * .996),
            (.1530, radius * .978), (.1560, radius * .925),
            (.1590, neck * 1.035), (.1610, neck), (.1642, neck),
        ]
        self.stations = [(z * self.zscale, r) for z, r in raw]
        self.datum = .0010 * self.zscale  # same correction applied to body parts

    def z_of(self, profile_value):
        return profile_value * self.zscale - self.datum

    def radius_at(self, profile_value):
        z = profile_value * self.zscale
        stations = self.stations
        if z <= stations[0][0]:
            return stations[0][1]
        for (z0, r0), (z1, r1) in zip(stations, stations[1:]):
            if z <= z1:
                f = (z - z0) / (z1 - z0)
                return r0 + f * (r1 - r0)
        return stations[-1][1]

    def normal_at(self, profile_value):
        """Outward normal in world axes for a point at ``profile_value`` height."""
        z = profile_value * self.zscale
        stations = self.stations
        z = min(max(z, stations[0][0] + 1e-6), stations[-1][0] - 1e-6)
        for (z0, r0), (z1, r1) in zip(stations, stations[1:]):
            if z <= z1:
                dr, dz = r1 - r0, z1 - z0
                nr, nz = dz, -dr
                length = math.hypot(nr, nz) or 1.0
                return nr / length, nz / length
        return 1.0, 0.0


def _build_beads(cfg, surface, template_verts, template_faces):
    """Sample bead positions with banded density, varied sizes and drips."""
    cine = _section(cfg, "CINEMATIC")
    count = int(cine.get("droplet_count", 620))
    seed = int(cine.get("droplet_seed", 7))
    rng = random.Random(seed)

    z_min, z_max = .0100, .1600
    bands = [(.0100, .0480, 1.30), (.0480, .1100, 1.00),
             (.1100, .1480, 0.60), (.1480, .1600, 0.85)]
    buckets = [(0.60, .00035, .00070), (0.28, .00070, .00130),
               (0.09, .00130, .00220), (0.03, .00220, .00320)]

    def pick_band():
        weights = [w * (b - a) for a, b, w in bands]
        total = sum(weights)
        x = rng.random() * total
        for (a, b, w), wt in zip(bands, weights):
            if x <= wt:
                return rng.uniform(a, b)
            x -= wt
        return rng.uniform(z_min, z_max)

    def pick_size(zv):
        x = rng.random()
        for weight, lo, hi in buckets:
            if x <= weight:
                base = rng.uniform(lo, hi)
                break
            x -= weight
        else:
            base = rng.uniform(.00035, .00070)
        coalesce = 1.0 + 0.22 * (1.0 - (zv - z_min) / (z_max - z_min))
        return base * coalesce

    placed = []  # (z, theta, size)
    verts, faces = [], []

    def add_bead(position, normal, size, flat, rng_roll=None):
        nonlocal verts, faces
        if rng_roll is None:
            rng_roll = rng.random
        angle = rng_roll() * math.tau
        quat = Vector(normal).to_track_quat("Z", "Y")
        rot = quat.to_matrix().to_4x4()
        scale = Matrix.Diagonal((size, size, size * flat, 1.0))
        center = Vector(position) - Vector(normal) * (0.30 * size * flat)
        matrix = Matrix.Translation(center) @ rot @ scale
        base = len(verts)
        verts.extend(matrix @ Vector(v) for v in template_verts)
        faces.extend(tuple(i + base for i in f) for f in template_faces)
        return angle

    # Body beads with spacing rejection.
    attempts = 0
    while len(placed) < count and attempts < count * 40:
        attempts += 1
        zv = pick_band()
        theta = rng.random() * math.tau
        size = pick_size(zv)
        radius = surface.radius_at(zv)
        ok = True
        for (z2, t2, s2) in placed[-260:]:
            dz = (zv - z2) * surface.zscale
            dt = abs(theta - t2) % math.tau
            dt = min(dt, math.tau - dt)
            dist = math.hypot(dz, radius * dt)
            if dist < 0.85 * (size + s2):
                ok = False
                break
        if not ok:
            continue
        placed.append((zv, theta, size))
        nr, nz = surface.normal_at(zv)
        pos = (radius * math.cos(theta), radius * math.sin(theta), surface.z_of(zv))
        normal = (nr * math.cos(theta), nr * math.sin(theta), nz)
        flat = rng.uniform(0.50, 0.72)
        add_bead(pos, normal, size, flat)

    # Drip streaks beneath a few of the largest beads on the near-vertical wall.
    drips = 0
    for zv, theta, size in list(placed):
        if size < .00125 or zv > .1420 or drips >= int(cine.get("drip_count", 26)):
            continue
        if rng.random() > 0.22:
            continue
        drips += 1
        length = size * rng.uniform(2.2, 3.4)
        z_tip = max(.0120, zv - length / surface.zscale * 0.9)
        z_mid = (zv + z_tip) / 2
        radius = surface.radius_at(z_mid)
        nr, nz = surface.normal_at(z_mid)
        pos = (radius * math.cos(theta), radius * math.sin(theta), surface.z_of(z_mid))
        n = Vector((nr * math.cos(theta), nr * math.sin(theta), nz)).normalized()
        down = Vector((0, 0, -1.0))
        down = (down - n * down.dot(n)).normalized()
        x_axis = down.cross(n).normalized()
        rot = Matrix.Identity(4)
        rot.col[0] = (x_axis.x, x_axis.y, x_axis.z, 0.0)
        rot.col[1] = (down.x, down.y, down.z, 0.0)
        rot.col[2] = (n.x, n.y, n.z, 0.0)
        width = size * 0.55
        thickness = size * 0.55 * 0.62
        center = Vector(pos) - n * (0.30 * thickness)
        matrix = Matrix.Translation(center) @ rot @ Matrix.Diagonal((width, length / 2, thickness, 1.0))
        base = len(verts)
        verts.extend(matrix @ Vector(v) for v in template_verts)
        faces.extend(tuple(i + base for i in f) for f in template_faces)

    # Lid scatter: small beads over the top disc, gently weighted to the rim.
    lid_z = surface.z_of(.16645)
    lid_radius = .0268
    for _ in range(int(cine.get("lid_droplets", 70))):
        rr = lid_radius * (rng.random() ** 0.72)
        theta = rng.random() * math.tau
        size = rng.uniform(.00035, .00110) * (1.0 + 0.5 * (rr / lid_radius))
        if rng.random() < 0.05:
            size *= 1.9
        pos = (rr * math.cos(theta), rr * math.sin(theta), lid_z)
        add_bead(pos, (0, 0, 1.0), size, rng.uniform(0.42, 0.58))
    return verts, faces


def _build_plinth_beads(cfg, surface, template_verts, template_faces, verts, faces):
    rng = random.Random(int(_section(cfg, "CINEMATIC").get("droplet_seed", 7)) + 31)
    for _ in range(9):
        rr = rng.uniform(.042, .075)
        theta = math.radians(-170 + rng.random() * 160)
        size = rng.uniform(.0005, .0015)
        flat = rng.uniform(0.42, 0.60)
        pos = Vector((rr * math.cos(theta), rr * math.sin(theta), .0004))
        quat = Vector((0, 0, 1)).to_track_quat("Z", "Y")
        matrix = Matrix.Translation(pos - Vector((0, 0, .30 * size * flat))) @ quat.to_matrix().to_4x4() @ Matrix.Diagonal((size, size, size * flat, 1.0))
        base = len(verts)
        verts.extend(matrix @ Vector(v) for v in template_verts)
        faces.extend(tuple(i + base for i in f) for f in template_faces)


def build_condensation(cfg, materials, parts, plinth: bool = False):
    """Create the merged bead mesh and parent it to the can rig."""
    import bmesh

    can = _section(cfg, "CAN")
    surface = _Surface(can)
    template_verts, template_faces = _sphere_template()

    verts, faces = _build_beads(cfg, surface, template_verts, template_faces)
    if plinth:
        _build_plinth_beads(cfg, surface, template_verts, template_faces, verts, faces)

    mesh = bpy.data.meshes.new("CAN_CondensationMesh")
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new("CAN_Condensation", mesh)
    collection = bpy.data.collections.get("CAN_DETAILS") or bpy.context.scene.collection
    collection.objects.link(obj)
    mesh.materials.append(materials.get("condensation"))

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True

    root = parts.get("root")
    if root is not None:
        obj.parent = root
        obj.location.z -= surface.datum
    obj["purpose"] = "Procedural water condensation; regenerate with scripts/condensation.py"
    obj["bead_count"] = len(faces) // 96  # template emits 96 faces per closed shell
    return obj
