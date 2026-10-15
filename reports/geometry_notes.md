# Can geometry module

`scripts/geometry.py` implements `build_can(cfg, materials) -> dict` for the
supervisor's integration script. It creates or reuses `CAN_GEOMETRY`,
`CAN_DETAILS`, `CAN_SOURCE`, and `SIMULATION`, and returns `root`, `body`,
`bottom`, `clean_source`, `lid`, `tab`, `panel`, and `collider` (plus `rim` and
`rivet`). `body` and `bottom` are separate closed meshes split at the lower
barrel station; each has a flat annular mating face. `clean_source` preserves
the complete hollow shell, hidden in `CAN_SOURCE`. It does not clear the scene,
save a blend, render, or configure physics.

## Defaults and editable dimensions

The current shared config uses radius (33 mm), height (157.23 mm), neck radius
(28 mm), nominal body wall (0.12 mm), label bottom/top (4 mm/152.23 mm), and
angular resolution (256). A separate 500 ml config preset remains available at
168 mm height. The body profile enforces a 0.18 mm minimum body-wall return;
the nominal config wall is a target setting, not a measured wall drawing.
All coordinates are metres. Vertical features scale with configured height;
the radius, neck, label span, and opening dimensions remain independently
configurable or fixed to their current tooling approximation. The silhouette
has a concave bottom dome and foot ring, straight barrel, tapered shoulder,
reduced neck, folded seam, and returned interior wall. Body UVs put U=.5 at
front (-Y), the seam at +Y, and V=0/1 at configured label bottom/top.

The top is a separate disk with a baked rounded-rectangle boolean opening,
rolled bead, shallow emboss ring, independent hinged scored panel, and stamped
pull tab. The tab has two boolean-punched holes, separate rivet, and a raised
spine. `CAN_Rig["opening"]` drives the panel down through the aperture and the
tab lever moves; `CAN_Rig["fill_level"]` is exposed for the static liquid builder.
Geometry is seated at the rig's z=0 base using a 1 mm profile datum offset; the
root itself stays at the floor.
The hidden `SIM_Can_Collider` is a separate closed radial shell with an
approximately 1.5 mm inward offset on its inner return. It is a collider
template. The delivered dynamic scene uses thicker dedicated native effectors
from `liquid_setup.py`; see `fluid_notes.md` and the supervisor QA report.

## Approximations

The production brief's supplied image indicates the US JUICE artwork family,
but geometry alone cannot prove the exact package revision. The supervisor's
research update identifies 473 ml / 66 mm diameter / 157.23 mm height as the
best matching standard-can envelope; that is a reasoned regional-variant
inference. The geometry defaults follow the supervisor's revised shared
config. Shoulder radii, rolled seams, dome depth, neck bead,
opening size and position, panel outline, tab stamping, rivet and embossing are
procedural mechanical approximations, not verified factory drawings. A real
through opening is present in the lid; opening mechanics are deterministic
drivers, not a physically simulated score fracture.

## Verification

Built successfully in Blender 5.2.2 background mode using a lightweight smoke
script with the 473 ml envelope. Body, bottom dome, clean source, and collider
each had zero non-manifold edges and zero wire edges; the base reached z=0 and
the component mating bounds matched. Boolean apertures and opening drivers also
passed. These specialist checks cover construction. The supervisor separately
rendered and inspected the final views, tested the mechanism with rays,
appended the asset into an empty scene, and baked the dedicated physics
proxies. Final verification is recorded in `qa_report.md`.
