"""Build a replaceable, deprojected interim wrap from the supplied can render.

The source is a front product render, not package artwork.  This script maps its
visible cylindrical front back to a flat label image.  Only the visible front
half is populated; the rear is a quiet turquoise field rather than invented
pack copy. Requires Pillow only.

Run from any directory:
    python MangoLoco3D/scripts/prepare_artwork.py
"""
from pathlib import Path
from PIL import Image, ImageChops
import math

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/references/user_reference.png"
DEST = ROOT / "assets/textures/mango_loco_wrap.png"

# The reference can center and silhouette were measured from the 2200 px image.
# Using a row profile also compensates for the shoulder and bottom taper.
CENTER_X = 1100.0
Y_TOP = 86.0
Y_BOTTOM = 2080.0
RADIUS_PROFILE = (
    (65, 380), (90, 393), (120, 403), (150, 425), (200, 459),
    (250, 470), (300, 470), (450, 468), (700, 463), (950, 460),
    (1200, 456), (1500, 450), (1700, 447), (1900, 443),
    (2000, 437), (2075, 380), (2080, 374),
)
WIDTH, HEIGHT = 4096, 2048
FRONT_HALF_ANGLE = math.radians(84.0)
TURQUOISE = (0, 181, 210, 255)
DELIGHT_CYAN = True


def radius_at(y: float) -> float:
    for (y0, r0), (y1, r1) in zip(RADIUS_PROFILE, RADIUS_PROFILE[1:]):
        if y <= y1:
            f = max(0.0, min(1.0, (y - y0) / (y1 - y0)))
            return r0 + f * (r1 - r0)
    return RADIUS_PROFILE[-1][1]


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Reference image not found: {SOURCE}")
    source = Image.open(SOURCE).convert("RGB")
    if source.size != (2200, 2200):
        raise ValueError(f"Expected the inspected 2200x2200 reference, got {source.size}")
    if DELIGHT_CYAN:
        # Remove the rendered light gradient only from strongly saturated cyan
        # ink. Keep all lettering, white bones, black outlines and orange art.
        # This is color-key cleanup of observed pixels, not synthesized artwork.
        h, sat, val = source.convert('HSV').split()
        mh = h.point(lambda x: 255 if 119 <= x <= 144 else 0)
        ms = sat.point(lambda x: 255 if x >= 155 else 0)
        mv = val.point(lambda x: 255 if x >= 110 else 0)
        mask = ImageChops.multiply(ImageChops.multiply(mh, ms), mv)
        source.paste(Image.new('RGB', source.size, TURQUOISE[:3]), (0, 0), mask)

    # Centered front occupies 168 degrees of the wrap (U=.2667..7333).
    # A mesh warp applies x = center + radius(z) * sin(theta), which is the
    # inverse of the near-orthographic cylindrical projection in the reference.
    output = Image.new("RGBA", (WIDTH, HEIGHT), TURQUOISE)
    left = round(WIDTH * (0.5 - FRONT_HALF_ANGLE / (2 * math.pi)))
    right = round(WIDTH * (0.5 + FRONT_HALF_ANGLE / (2 * math.pi)))
    nx, ny = 168, 96
    mesh = []
    for yi in range(ny):
        dy0 = yi * HEIGHT // ny
        dy1 = (yi + 1) * HEIGHT // ny
        # Destination image is top-down; the source is sampled at the same
        # top-down height in the original render.
        sy0 = Y_TOP + (dy0 / HEIGHT) * (Y_BOTTOM - Y_TOP)
        sy1 = Y_TOP + (dy1 / HEIGHT) * (Y_BOTTOM - Y_TOP)
        ry0, ry1 = radius_at(sy0), radius_at(sy1)
        for xi in range(nx):
            local_x0 = xi * (right - left) // nx
            local_x1 = (xi + 1) * (right - left) // nx
            dx0, dx1 = left + local_x0, left + local_x1
            theta0 = ((dx0 / WIDTH) - 0.5) * (2 * math.pi)
            theta1 = ((dx1 / WIDTH) - 0.5) * (2 * math.pi)
            sx00 = CENTER_X + ry0 * math.sin(theta0)
            sx10 = CENTER_X + ry0 * math.sin(theta1)
            sx01 = CENTER_X + ry1 * math.sin(theta0)
            sx11 = CENTER_X + ry1 * math.sin(theta1)
            # Pillow's quad order is upper-left, lower-left, lower-right,
            # upper-right (the order used by Image.QUAD as well).
            mesh.append(((local_x0, dy0, local_x1, dy1),
                         (sx00, sy0, sx01, sy1, sx11, sy1, sx10, sy0)))

    front = source.transform(
        (right - left, HEIGHT), Image.Transform.MESH, mesh,
        resample=Image.Resampling.BICUBIC,
    )
    output.alpha_composite(front.convert("RGBA"), (left, 0))
    # Seam-safe extension: a two-pixel wrap blend at each angular boundary.
    # The populated front edge fades only into the same base color used on the
    # unknown back.  This avoids an abrupt color seam on a turntable.
    px = output.load()
    fade = 12
    # The horizontal seam fade is intentionally tiny.
    for y in range(HEIGHT):
        for i in range(fade):
            a = (i + 1) / (fade + 1)
            for edge_x, inward_x in ((left + i, left + fade), (right - 1 - i, right - 1 - fade)):
                c = px[inward_x, y]
                px[edge_x, y] = tuple(round(TURQUOISE[k] * (1 - a) + c[k] * a) for k in range(4))

    DEST.parent.mkdir(parents=True, exist_ok=True)
    output.save(DEST, format="PNG", optimize=True)
    print(f"Wrote {DEST} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
