# Product studio module

`scripts/studio.py` implements `build_studio(cfg) -> dict` and returns camera
objects under `front`, `three_quarter`, `side`, `top`, and `hero`. The module
adds objects to `STUDIO` and `CAMERAS`, configures Cycles on CPU, and never
clears the scene or writes a `.blend` file. One Blender unit is one metre; the
can bottom remains at `z=0` and the plinth top is aligned with it.

The portrait cameras use a 76–82 mm lens and frame the can at roughly three
quarters of the image height. The hero camera has a mild three-quarter angle and
slight downward view. `top` is a square, orthographic close-up intended to show
the lid, tab, and drinking aperture sharply. All cameras start at a 1 mm clip
distance. The preview output size and Cycles sample counts come from the
`RENDER` section of `config.py`; final resolution remains available there for
the supervisor's hero render.

The rig uses a warm ivory cyclorama with a 160 mm radial cove, 650 mm floor radius, and surrounding vertical walls. This surrounds all cameras with a continuous floor-to-wall sweep. The side
preview exposed the boundary of the earlier single-wall studio; the supervisor
replaced it with a 360-degree cove. A two-step beveled plinth
uses subdued matte burnt orange to separate its edge from both the ivory sweep
and the can. Four rectangular area lights provide a warm key, cool fill, warm
rear strip, and restrained front reflection card. The first integrated preview
showed severe clipping, so their powers are reduced 100-fold to 1.10, 0.42,
0.66, and 0.18 W respectively. Their objects have `studio_control` metadata;
edit their positions, colors, dimensions, or native Light Properties power
(`data.energy`) to tune reflections. `power_watts` records the initial power
as metadata; it does not drive the light. The world remains a restrained warm fill.

Render defaults are Cycles CPU with denoising, AgX medium-high contrast, 32
preview samples, and 160 final samples (overridable in `config.py`). GPU is not
selected because the production brief records the NVIDIA driver as unavailable.
The supervisor reviewed early previews and corrected clipping, the horizon,
metal grain scale, color cast, and the label background. Final views and
their validation status are recorded in `qa_report.md`.
