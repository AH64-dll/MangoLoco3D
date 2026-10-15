# Project: Production-Ready Monster Mango Loco 3D Asset in Blender

## Your Role

You are the lead technical artist and supervisor of a multi-agent 3D production pipeline.

Your task is to build a highly realistic, professionally structured, reusable Blender 3D asset of a **Monster Energy Mango Loco can**, using the provided reference image.

This is not merely a visualization task. The asset must be suitable for commercial-style product renders, animation, liquid pouring, splashes, and future destruction effects.

**Core principle:** Build a real, editable, modular Blender project. Do not substitute AI-generated images, fake render composites, or nonfunctional demonstration geometry for actual 3D assets.

## Technical Approach

Use:

- Blender Python API (`bpy`) for procedural asset construction.
- Blender MCP, if available, for live inspection, manipulation, and visual verification.
- Cycles for high-quality final renders.
- Geometry Nodes and non-destructive modifiers where appropriate.
- Blender's native Mantaflow liquid system for physical liquid simulation.
- A modular Python codebase with reproducible scene construction.

Use image-to-3D generation only if it has a clear advantage for a specific component. Do not use it as a replacement for precise manufactured geometry.

## Phase 1 — Inspection and Research

Before modeling:

1. Inspect the provided reference image and all available project assets.
2. Determine the installed Blender version and available tools.
3. Research the exact appearance and proportions of Monster Mango Loco.
4. Gather additional trustworthy reference images for the front, back, sides, top, and bottom if internet access is available.
5. Search for usable high-resolution packaging artwork or a legitimate full-wrap texture.
6. Identify uncertain packaging details rather than inventing them.
7. Establish a consistent real-world measurement system.

Do not confuse different regional can sizes or packaging variants.

If a dimension cannot be verified, expose it as a configurable parameter and label the chosen default as an approximation.

The provided low-resolution image is a visual reference, not a sufficient final texture.

## Phase 2 — Agent Organization

If subagents are available, organize four specialists:

**Agent A — Product Geometry**
Responsible for accurate topology, cylindrical profile, bevels, rim details, bottom concavity, interior cavity, lid, pull tab, and openable drinking aperture.

**Agent B — Packaging and Materials**
Responsible for texture references, UV mapping, packaging artwork, metal PBR materials, printed graphics, and validation against the reference.

**Agent C — Studio and Rendering**
Responsible for lighting rigs, cameras, professional product photography composition, render settings, and visual presentation.

**Agent D — Fluid Physics**
Responsible for mango liquid geometry, shaders, simulation setup, collision geometry, pouring tests, simulation cache management, and reusable animation setups.

The supervisor must define interfaces, file ownership, and object-naming conventions before delegating work.

Allow specialists to work concurrently on isolated scripts or scene files.

**Never allow multiple agents to modify the same live Blender scene simultaneously.**

Only the supervisor should perform the final integration.

## Phase 3 — Build the Can

Create physically credible aluminum can geometry.

Required independent components:

- Main cylindrical aluminum body
- Convex/curved shoulder transition
- Concave bottom
- Top metallic lid and rolled rim
- Pull tab with opening mechanism
- Actual drinking opening
- Inner cavity
- Separate collision mesh for liquid physics

Use realistic surface transitions and smooth shading without destroying the silhouette.

The can must look correct in close-up product shots, including at grazing angles.

Use clean topology and stable UV coordinates.

The printed label artwork must wrap naturally around the body.

Avoid stretched logos, distorted lettering, visible texture seams on the front, or fabricated unreadable packaging text.

Include both closed and opened configurations.

Keep the original clean geometry intact.

## Phase 4 — Materials and Texturing

Create high-quality physically based materials.

The aluminum must exhibit realistic metallic reflections and controlled roughness.

The printed packaging should have realistic ink characteristics, sharp details, and correct color response under studio lighting.

Do not make the can look like a plastic bottle or an excessively reflective chrome object.

Use high-resolution image textures wherever good source assets are available.

For any artwork that cannot be faithfully reconstructed, record the limitation clearly and keep the UV/material system ready for future replacement.

Create a reusable mango-liquid material with:

- Natural mango-orange coloration
- Plausible transparency and light absorption
- Subtle internal scattering where useful
- Adjustable opacity and roughness
- Optional subtle bubbles
- A physically coherent appearance rather than glowing orange glass

The liquid material should work in both static and dynamic scenes.

## Phase 5 — Professional Studio Setup

Construct a reusable product photography environment.

Include:

- A clean studio platform or pedestal
- Large softbox-style area lights
- Adjustable key, fill, and rim lights
- A suitable background or world shader
- Contact shadows and controlled reflections
- Front hero camera
- Three-quarter camera
- Side camera
- Top-detail camera
- Optional turntable animation rig

Prefer elegant, restrained lighting over exaggerated glowing effects.

The primary deliverable should resemble a polished commercial product photograph.

Produce preview renders early and repeatedly.

## Phase 6 — Reusable Mango Liquid System

Design two interchangeable liquid representations.

### A. Static Liquid

Create a render-friendly liquid volume inside the can.

It must be independently controllable and must not be permanently merged with the aluminum geometry.

Allow the user to adjust fill level and material parameters.

Use this representation for still renders and inexpensive animations.

### B. Dynamic Liquid

Configure a working Mantaflow liquid simulation.

Requirements:

- A valid liquid domain
- A suitable initial internal liquid volume
- Collision effectors for the can's interior
- An opening through which the liquid can escape
- Adjustable viscosity and surface behavior
- Animated can movement for a pouring demonstration
- A correctly configured simulation cache directory
- Liquid mesh generation for rendering
- Optional secondary spray and droplets

Pay particular attention to domain scale, collision thickness, and voxel resolution.

Use dedicated hidden simulation collision proxies if the real aluminum geometry is too thin for stable fluid collisions.

Preserve realistic render geometry separately.

Do not claim that a fluid simulation works until it has actually been baked and visually inspected.

Create an initial short pouring animation with a small domain and low-cost simulation settings.

Only increase resolution after the test is stable.

Avoid spending hours on high-resolution simulations before confirming the geometry, opening, and collision setup.

## Phase 7 — Future Destruction Compatibility

Prepare the asset for later animation scenarios:

1. A can tipping over and spilling liquid.
2. A can being opened and pouring into a glass.
3. A can falling and producing a splash.
4. A can being crushed.
5. A can bursting with liquid expelled outward.

Do not fully simulate every scenario during this initial project.

Instead, design the architecture so each scenario can be implemented without rebuilding the source model.

Keep optional damaged or fractured geometry separate.

Where necessary, plan a controlled workflow combining rigid-body animation with liquid simulation.

Avoid assuming full bidirectional coupling between liquid and rigid-body solvers.

## Phase 8 — Automated Verification

Create a repeatable build and validation process.

The supervisor must:

1. Execute the scene-building scripts.
2. Check Blender console output for errors.
3. Verify that all required objects and collections exist.
4. Inspect geometry and modifier states.
5. Detect missing textures and incorrect paths.
6. Render front, three-quarter, side, and top views.
7. Compare those renders with the references.
8. Inspect the quality of packaging artwork and reflections.
9. Verify that the can opens correctly.
10. Bake a short pouring test.
11. Inspect several frames of the simulated liquid.
12. Fix visible issues and repeat tests.

Visual inspection is mandatory. A script completing successfully is not evidence of visual quality.

Use an iterative render → inspect → correct → render loop until the result meets the quality requirements.

If visual inspection tools are unavailable, explicitly report that limitation rather than claiming the asset has been visually verified.

## Phase 9 — Performance

Detect available CPU, RAM, GPU, and VRAM.

Select conservative defaults suitable for the actual hardware.

Use low-resolution preview renders and simulations during development.

Keep expensive liquid simulations disabled in the default product-render scene.

Make final-quality settings accessible through configuration.

Do not run multiple heavy simulation bakes or GPU renders concurrently.

Use disk-based cache directories and document their storage requirements.

## Phase 10 — Project Architecture

Organize the project approximately as follows:

```text
MangoLoco3D/
  assets/
    references/
    textures/
    hdri/
  scripts/
    geometry.py
    materials.py
    studio.py
    liquid_setup.py
    animation.py
    build_project.py
    validate.py
  blender/
    mango_loco_master.blend
    mango_loco_studio.blend
    mango_loco_liquid.blend
  cache/
    liquid/
  renders/
    previews/
    final/
  reports/
    qa_report.md
  README.md
```

Adjust this structure when technically justified, but preserve modularity and clear ownership.

Keep texture references portable and avoid absolute paths tied to one machine.

The main asset should be reusable without depending on the original agent conversation.

## Final Deliverables

Produce:

**1. Master Asset**
A clean Blender project containing the completed can, materials, opening mechanism, and static liquid.

**2. Studio Scene**
A professional reusable lighting and camera setup with high-quality product renders.

**3. Physics Scene**
A working initial liquid simulation with a verified pouring test.

**4. Procedural Scripts**
The Python source code needed to rebuild and modify the scenes.

**5. Preview Renders**
Front, three-quarter, side, top-detail, and liquid-action previews.

**6. QA Report**
Document the visual quality, reference accuracy, simulation status, remaining limitations, and recommended future improvements.

**7. Usage Instructions**
Explain how to change the artwork, fill level, lighting, animation, and physics settings.

## Acceptance Criteria

The project is not complete unless:

- The model resembles the intended Mango Loco product.
- The can is actual editable 3D geometry.
- Packaging graphics are correctly mapped.
- The model is visually convincing under professional studio lighting.
- The can has separate lid and opening components.
- The liquid exists as a separate asset.
- The physical pouring demonstration has been successfully tested.
- All important scripts can be rerun.
- The Blender files open without missing required dependencies.
- The final asset can be reused in other scenes.

## Execution Instructions

Start by inspecting the environment and references, then create a concise implementation plan.

Delegate independent tasks to subagents if available.

Begin production immediately after planning.

Prioritize the quality and accuracy of the base asset before expensive physics simulations.

Do not stop after creating a basic cylinder, a low-quality mockup, or a single attractive render.

Continue through implementation, rendering, inspection, debugging, and validation.

If a task is blocked by genuinely missing source artwork or hardware limitations, complete all independent work, clearly identify the blocker, and never fabricate successful validation results.

The goal is a polished, technically sound, reusable, animation-ready Blender asset—not just a pretty image.
