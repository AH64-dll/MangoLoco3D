# Supervisor QA — Mango Loco 3D asset

Date: 2026-10-11. Blender 5.2.2 LTS; all delivered imagery is rendered from editable Blender geometry using Cycles. Four specialist modules were integrated and reviewed by the supervisor; no generated product image, fake stream, or render composite replaces the asset.

## Current acceptance status

Master geometry, opening/fill controls, portability/reuse, studio visual review, and native initial pouring test: PASS. The playback preview is encoded and fully decodes without errors. All required deliverables are ready; the portable archive is built from these verified files.

## Verified master asset

The saved master file opens successfully. Required collections and objects exist. The body, separate concave bottom, preserved complete hollow source, lid, rolled rim, scored panel, pull tab, rivet, and static liquid remain independent. Inspected can meshes have zero non-manifold edges. Printed faces have locally continuous cylindrical UVs (maximum U span 0.0039063); the seam is on the rear.

The aperture is a through-hole in the lid. A ray is blocked by the closed panel and passes through after opening; the lid does not block it. The control rotates the panel 0.92 radians and tab 0.62 radians at full opening. Static fill tests at 0.2 and 0.8 change the surface height from approximately 32.85 to 111.88 mm. The original shape and artwork remain available separately.

The 4096 x 2048 label is packed and has a portable relative path. Appending the three asset collections into a fresh empty Blender scene preserved the packed image, driver references, opening mechanism, and independently editable liquid. The optional linear turntable evaluates to 90 degrees at frame 31.

Machine evidence: `validation_mango_loco_master.json` and `reuse_verification.json`.

## Studio visual review

The supervisor inspected the rebuilt front, three-quarter, side, and top previews, opened top detail, and the final 1440 x 1800 / 160-sample Cycles hero. The model follows the supplied silhouette and front graphic, the front seam is absent, and the main text is legible. The separate rim reflects the softboxes; metal microtexture is restrained. The can rests on a two-level burnt-orange pedestal with contact shadows against a warm ivory sweep.

Render review exposed and corrected overpowered lights, a coarse metal bump, a hard horizon in the side camera, and vertical label repetition at the neck. The final studio uses a surrounding radial cove and clamps label V to its edge while allowing U to wrap. The side preview makes the incomplete rear artwork visible. Small inherited highlights in the reference texture and approximate end tooling remain close-up accuracy limits.

Views: `renders/previews/front.png`, `three_quarter.png`, `side.png`, `top.png`, `top_opened.png`; primary image: `renders/final/hero.png`.

## Physics bake and visual review

The final `pour_verified_v4` cache contains **64 data frames and 64 surface meshes**, totaling **58.7 MiB**. Native data and mesh flags are both baked. The full bake took **583.74 seconds** on this CPU. The domain, initial geometry source, animated thick can effectors, real perforated lid, receiver, and ground were rebuilt and executed in Blender. No external emitter or modeled stream was used.

The supervisor inspected real Cycles renders at frames **8, 20, 32, 44, and 64**. The upright stage has no visible exterior liquid; evaluated meshes at frames 1 and 8 also report zero vertices outside the lower can envelope. The raised can clears the receiver rim: the opening finishes approximately 25 mm above it. Frame 44 shows the first drops; frame 64 shows a continuous stream through the actual aperture and liquid collecting inside the bowl. The can end remains above the glass rather than inserting into it.

The validator reads the actual cached surface at seven frames. It finds liquid in the receiver at frames 44, 56, and 64, with 1,966 receiver-region vertices at frame 64. The full can fits within the domain across all 64 animation frames. The delivered physics file opens on frame 64; return to frame 1 to play the sequence.

**Resolution limits:** this is a verified initial pour, not final close-up fluid cinematography. At 96 cells (approximately 3.33 mm voxels), the surface has visible facets, broken droplets, and a few isolated particles around the moving can. Source clearance and the approximately 6 mm collision wall reduce the simulated capacity relative to the real aluminum cavity. Fill is a height setting, not calibrated millilitres. Secondary spray, gas/air coupling, and full emptying of the can are not validated. The next improvement is a 160–192-cell bake with finer surface meshing and adjusted collision clearance. Preserve this stable test before making those changes.

Earlier tests were rejected for gross upright leakage or the can mouth sitting inside the receiver. Source expansion, mesh dilation, collider clearance, viscosity API selection, and the pour pose were corrected before this final result. Development caches are excluded from the delivery archive.

Machine evidence: `bake_result_mango_loco_liquid.json`, `physics_preflight.json`, and `validation_mango_loco_liquid.json`. Action previews: `renders/previews/pour_008.png` through `pour_064.png`.

## Playback export

`renders/final/pour_preview.mp4` is H.264, 384 x 480, 24 fps, 64 frames (2.667 seconds), rendered from every native cached frame at 16 Cycles samples. It is a motion preview; full-resolution stills and editable native scenes are delivered separately. FFprobe confirms the frame count and dimensions, and a complete decode reports no errors. The supervisor additionally inspected the stream at frame 56 of this sequence.

## Reference accuracy

The turquoise color family, orange claw/title, JUICE presentation, and front illustration follow the supplied 2200 x 2200 image. The dimensional target is the inferred US 473 ml / 66 mm diameter / 157.23 mm standard-can envelope. Exact capacity is not visible in the supplied image; the regional choice is an inference. The mechanical cross-section, shoulder, end tooling, wall thickness, tab, and score are procedural approximations, not factory drawings. See `artwork_sources.md` for research links.

The observed front is cylindrically deprojected. Saturated cyan background shading is normalized to reduce duplicated lighting. Some source shading and finite raster detail remain in the artwork. Authentic full-wrap art was not found; the unobserved rear is plain turquoise, and ingredients, barcode, and regulatory copy are not invented. Rear packaging fidelity is incomplete and requires a replacement wrap. This limitation does not prevent editing, rendering, or simulation.

## Performance and reproducibility

The host has a Ryzen 5 8645HS (6 cores / 12 threads), approximately 22 GiB RAM, and an RTX 4050 whose NVIDIA driver was unavailable to Blender. Cycles uses 8 CPU threads; heavy jobs run sequentially. Preview settings are 32 samples at 720 x 900, with square top details. Final settings are 160 samples at 1440 x 1800. The default master/studio contain no active fluid domain.

Scene builders, artwork preparation, saved-scene rendering, validation, opening/fill controls, and the turntable helper have executed successfully. The batch launcher bypasses a sandbox audio-cleanup hang only after successful saves/renders. A read-only Blender extension-cache warning did not affect scene building or rendering. The procedural source and original user reference are included.

## Future effects

Crush, burst, drop, and rigid-body tipping scenarios are planned around copies of the preserved clean source and independent solver proxies. They have not been simulated in this initial delivery. Bake prescribed or rigid-body motion first, then Mantaflow; full bidirectional coupling is not assumed. Higher-resolution splashes and secondary spray are follow-up work after the initial pour is stable.
