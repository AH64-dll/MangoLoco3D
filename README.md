# Mango Loco editable Blender asset

Open the [studio scene](blender/mango_loco_studio.blend), [reusable master](blender/mango_loco_master.blend), or [physics scene](blender/mango_loco_liquid.blend). Built with Blender **5.2.2 LTS** and Cycles. If using the ZIP, extract the complete folder first. The texture is packed in each file; retain the folder structure to keep external artwork and simulation caches portable.

The supplied image shows the **JUICE** presentation. The default is the inferred 473 ml envelope, 66 mm diameter × 157.23 mm tall, using [Crown's dimensions](https://www.crowncork.com/beverage-packaging/products/beverage-cans/16oz-473ml-standard) and [Monster's US 16 oz product page](https://www.monsterenergy.com/en-us/energy-drinks/juice-monster/mango-loco/). The capacity cannot be read from the supplied image. The separate `CAN_500ML` preset is 168 mm tall; it needs matching regional artwork.

The front graphic is reconstructed from the supplied reference, with cylindrical deprojection and cyan color cleanup. **The unseen rear is plain turquoise.** Authentic back-panel artwork, barcode and regulatory copy are unavailable. This is an editable product visualization asset with a replaceable texture, not press-ready packaging. See `reports/artwork_sources.md` and `reports/qa_report.md` for accuracy and validation limits.

[Final hero image](renders/final/hero.png) · [Pour playback](renders/final/pour_preview.mp4) · [Supervisor QA](reports/qa_report.md)

**Repository note.** Git tracks the scripts, scenes, showcase renders and reports; the verified simulation cache ships as the `v1.0` release asset. Frame sequences (`renders/animation`), development renders (`renders/dev`), simulation caches and intermediate test scenes are regenerable from the scripts and are deliberately not tracked.

## Controls in Blender

- Select `CAN_Rig` → Object Properties → Custom Properties. `opening` changes from 0 (closed) to 1 (open), moving the tab and pushing the scored panel into the actual aperture. `fill_level` controls the independent static liquid's height from 0 to 1. This is a height fraction, not a calibrated millilitre readout. Use the master or studio for direct controls; the physics scene keys the opening and uses a baked fill.
- Cameras: `CAM_Hero`, `CAM_Front`, `CAM_Three_Quarter`, `CAM_Side`, `CAM_Top_Detail`; physics adds `CAM_Pour`. Select a camera and use Ctrl+Numpad 0 to make it active.
- Adjust the named key, fill, rim and front-card area lights under `STUDIO`. Powers are tuned for a 16 cm product in metres. Keep the lights' physical scale and distance in mind when changing power.
- In the Shader Editor, the label material contains **Replace with licensed full-wrap art**. Replace its image and pack it with File → External Data → Pack Resources. The image is a complete wrap, front at U=.5, seam on the rear (+Y). Use a 2:1 image or adjust dimensions to your print template; the UV stays stable.
- The liquid material's Principled shader exposes color, roughness, transmission and subsurface weight; Volume Absorption controls depth coloration. No emission is used.

## Rebuild and render

Use Blender 5.2. Python 3 with Pillow is needed only to regenerate the supplied texture; it is already included and packed. FFmpeg is needed only to re-encode the optional playback video.

Commands below run from the parent workspace directory. Set `BLENDER_BIN=/path/to/blender` to override the detected local binary. The launcher keeps batch caches/config inside this project and disables audio. Python errors stop the batch with a nonzero status.

```bash
python3 MangoLoco3D/scripts/prepare_artwork.py
MangoLoco3D/scripts/run_blender.sh --python MangoLoco3D/scripts/build_project.py -- --mode master
MangoLoco3D/scripts/run_blender.sh --python MangoLoco3D/scripts/build_project.py -- --mode studio --render front,three_quarter,side,top
MangoLoco3D/scripts/run_blender.sh --python MangoLoco3D/scripts/build_project.py -- --mode studio --final --render hero
MangoLoco3D/scripts/run_blender.sh MangoLoco3D/blender/mango_loco_studio.blend --python MangoLoco3D/scripts/render_saved.py -- --cameras top --open 1
MangoLoco3D/scripts/run_blender.sh MangoLoco3D/blender/mango_loco_master.blend --python MangoLoco3D/scripts/validate.py
```

Modify `scripts/config.py` for envelope, fill, approximate tooling dimensions, render quality and solver settings. The radial cross-section is deliberately exposed in `geometry.py`; optionally supply `CAN['profile_points']` to replace the entire metre-scale profile. Other mechanical details are labeled approximations and can be edited directly in the corresponding geometry module. `prepare_artwork.py` exposes the measured image crop and silhouette profile; `DELIGHT_CYAN=False` preserves the source lighting gradient.

## Liquid scene

The physics file opens at frame 64 to show the stream; return to frame 1 to play. The scene uses a one-shot internal liquid volume, a native Mantaflow liquid domain, dedicated thick can-wall and perforated-lid collision meshes, and a separate visible receiving bowl. The aluminum render geometry stays independent. Frames 1–8 settle, 9–33 tip and lift the can 30 mm, and 33–64 hold. The aperture finishes about 25 mm above the receiver rim. This is an animated pouring test, rather than a rigid-body falling simulation. Default simulation runs at half time scale, so 64 playback frames show approximately 1.3 seconds of simulated time.

```bash
# Build to a NEW cache directory in config.py when changing physics.
MangoLoco3D/scripts/run_blender.sh --python MangoLoco3D/scripts/build_project.py -- --mode liquid --bake
MangoLoco3D/scripts/run_blender.sh MangoLoco3D/blender/mango_loco_liquid.blend --python MangoLoco3D/scripts/render_saved.py -- --cameras pour --frames 8,20,32,44,64
```

The final demonstration also includes `renders/final/pour_preview.mp4`, a 64-frame / 24 fps preview. To export it again from the real cached simulation:

```bash
MangoLoco3D/scripts/run_blender.sh MangoLoco3D/blender/mango_loco_liquid.blend --python MangoLoco3D/scripts/render_saved.py -- --cameras pour --frames 1:64 --samples 16 --width 384 --height 480 --out animation
ffmpeg -y -framerate 24 -start_number 1 -i MangoLoco3D/renders/animation/pour_%03d.png -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart MangoLoco3D/renders/final/pour_preview.mp4
```

The delivered cache is `cache/liquid/pour_verified_v4` relative to the saved physics file; the ZIP delivery contains it, and for a git clone it is provided as the `pour_verified_v4.zip` asset of the `v1.0` release (extract into `cache/liquid/`, or rebake). Data is baked first, then the surface mesh. Rebuilding the physics scene resets its cache flags; rebake after changing the domain, initial fill, effectors, aperture, animation or viscosity. Do not overwrite a cache while another Blender process is using it. Run one heavy bake or render at a time. The batch scripts exit explicitly after successful saves/renders to bypass an audio-cleanup hang in this sandbox; interactive Blender is unaffected. The delivered cache size is recorded in the QA report; budget **1–3 GB** for experiments, and check free space before increasing resolution. The 96-cell test is for validation; higher resolution is available through `SIM['resolution']` once a test is stable.

For interactive manual rebaking select `SIM_Liquid_Domain`, Physics → Fluid → Cache → Bake Data, then Bake Mesh. Scrub the cached scene before rendering. Static liquid is hidden in this scene and should remain hidden so it does not duplicate the baked surface. Collision proxies are hidden from the render and shown as wire geometry in the viewport.

## Reuse and later effects

File → Append from the master: append `CAN_GEOMETRY`, `CAN_DETAILS` and `LIQUID_STATIC` together so the rig references travel with the asset. The geometry, UVs, materials, opening drivers and liquid remain editable. Append `CAN_SOURCE` as well if you want the preserved complete hollow shell; it stays hidden while the modular body/base are visible. A separate unconfigured collider template is available in `SIMULATION`; the physics scene uses its own validated thick effectors. Avoid joining the components if you need the opening mechanism.

`animation.build_turntable(CAN_Rig, frames=120)` makes an optional linear turntable on a studio copy; it is disabled in the delivered default scene. Keep any damaged body under a new `DAMAGE_VARIANTS` collection while retaining the clean source. For crush, add shape keys/lattice or a separate deformation mesh and drive a matching thick liquid collider. For burst, fracture a copy, animate pieces, and bake an outward liquid source in a larger domain. For a drop or tip, bake rigid-body movement first, then use that fixed animation in Mantaflow. The solvers are not assumed to have full bidirectional coupling. These later scenarios are architecture plans, not completed destruction simulations.

Procedural modules: `geometry.py`, `materials.py`, `studio.py`, `liquid_setup.py`, `animation.py`; integration: `build_project.py`; checks: `validate.py`; cached rendering: `render_saved.py`; baking: `bake_liquid.py`. Original reference and task brief remain under `assets/references` and `reports`.
