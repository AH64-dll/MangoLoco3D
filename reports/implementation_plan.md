# Production plan and interfaces

The supplied brief is the acceptance contract. Preserve existing unrelated projects.

One Blender unit is one metre. Default envelope: 473 ml standard, diameter 66 mm, height 157.23 mm, based on Crown manufacturer specification. Monster US lists JUICE Mango Loco as 16 oz. Matching the supplied JUICE graphic to this size is an inference; source image has no visible capacity. 500 ml / 168 mm remains a separate config preset. Do not mix UK JUICED back-panel artwork. Mechanical detail dimensions remain approximations exposed in config.py.

Supervisor owns config.py, common.py, build_project.py, animation.py, validate.py, integration, all final .blend files, caches and renders. Specialists write isolated modules; only supervisor runs integrated Blender jobs. Collections: CAN_GEOMETRY, CAN_DETAILS, LIQUID_STATIC, SIMULATION, STUDIO, CAMERAS. Object prefixes CAN_, LIQ_, SIM_, STUDIO_, CAM_.

Geometry interface: geometry.build_can(cfg, materials) -> dict with root, body, lid, tab, panel, collider. Root CAN_Rig at base; label front toward -Y; UV U=.5 at front, seam +Y. Opening located toward -Y. Independent mechanics, real cavity; root properties opening and fill_level. Materials keys aluminum, label, tab, liquid, dark_metal. Open configuration uses actual aperture and hinged panel, no fake black hole.

Materials interface: materials.build_materials(root_path) -> material dict above. Document provenance and missing wrap regions; keep replaceable full-wrap image. No invented regulatory text.

Studio interface: studio.build_studio(cfg) -> camera dict front, three_quarter, side, top, hero. Ground at z=0; root at base. No scene clear or save in specialist modules.

Fluid interface: liquid_setup.build_static(cfg, materials, parts); liquid_setup.build_dynamic(cfg, materials, parts) builds Mantaflow domain, closed collision proxies with real opening, liquid geometry source and animated pouring can. Physically baked output must be inspected at several frames before claiming success.

1. Research variants and artwork, inspect tools/hardware.
2. Build editable body/lid/opening, portable materials and studio.
3. Render front, three-quarter, side and top; inspect and correct.
4. Bake small pouring test, inspect geometry and action frames, correct leaks or blocked opening.
5. Final Cycles hero render, clean master/studio/physics files, repeatable validators and user instructions.

Only one heavy rendering/baking job at once. CPU available; NVIDIA driver unavailable. Disk cache budget below 3 GB for initial test.
