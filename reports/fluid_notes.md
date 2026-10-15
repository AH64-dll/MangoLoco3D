# Native liquid implementation

The reusable still volume is `LIQ_Static_Fill` under `LIQUID_STATIC`. Its sealed mesh has a shape key driven by `CAN_Rig["fill_level"]`. This control is a height fraction, not a calibrated volume. The dynamic source uses the configured fill when rebuilding; changing the static control does not alter an existing bake.

## Delivered solver configuration

- Blender 5.2.2 Mantaflow LIQUID, MODULAR cache, OPENVDB data and BOBJECT mesh.
- 96 cells on the 320 mm longest domain axis: approximately 3.33 mm cells. Mesh scale 2 and mesh particle radius 1.0.
- Domain bounds: X -70..70 mm, Y -255..65 mm, Z -10..190 mm.
- Frames 1..64, 24 fps, time scale 0.5; CFL 2, FLIP ratio 0.97.
- Diffusion enabled, viscosity base 4 / exponent 6 (4e-6). The separate high-viscosity solver is disabled. Surface tension is 0 for this conservative coarse test.
- Initial internal source is GEOMETRY, not a continuing inflow. Surface distance is zero, source radius 25 mm, and emission is disabled at frame 9.
- Thick independent can-wall proxy: 36 mm outer / 30 mm inner barrel radius. The approximately 6 mm solver wall is deliberately thicker than the aluminum render wall.
- Separate 4 mm perforated lid proxy; 22.5 x 12.5 mm rounded aperture matches the visible lid. Can proxy surface distance 0.25 cells; effectors use three subframes.
- A real receiving bowl at Y=-213 mm and a solid ground collider collect the result.
- Can settles through frame 8, tips 110 degrees toward -Y and lifts 30 mm from frames 9..33, then holds through 64. Its aperture clears the receiver rim by approximately 25 mm. This is prescribed animation, not a rigid-body solve.

The static liquid is hidden in the physics file. Sources and can collision proxies are hidden from Cycles. Only the baked liquid surface and visible glass receiver render. No external emitter, modeled stream, or composited splash substitutes for the solver.

## Debugging and verification

The first full bake exposed source expansion, mesh dilation, and insufficient wall clearance: liquid appeared outside the upright can. Those results were rejected. The supervisor reduced source surface distance to zero, inset the source and solver interior, thickened the lid, reduced mesh particle radius, and corrected the viscosity API selection. A short eight-frame test was rendered to confirm initial containment before the final 64-frame bake.

The final bake and frame inspection results, timings, cache size, and remaining resolution limits are recorded in `qa_report.md` and the machine-readable validation report. A successful bake alone is not visual approval.

Rebake to a new directory after changing resolution, viscosity, aperture, initial volume, or animated effectors. At 96 cells the aperture is only about four cells across its short axis; this is an initial pouring demonstration, not a final close-up splash simulation. Use a stable 160..192-cell test next, enlarge the domain for outward splashes, and preserve the clean render geometry.
