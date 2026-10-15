"""Supervisor-owned reproducible integration. Run with Blender --python, see README."""
import sys, argparse, json, math
from pathlib import Path
import bpy
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config, geometry, materials, studio

def args():
    p=argparse.ArgumentParser()
    p.add_argument('--mode', choices=['master','studio','liquid','cinematic'],default='studio')
    p.add_argument('--preview',action='store_true')
    p.add_argument('--render',default='',help='Comma-separated camera names')
    p.add_argument('--final',action='store_true')
    p.add_argument('--open',type=float,default=0)
    p.add_argument('--bake',action='store_true')
    p.add_argument('--test-frames',type=int,default=0,help='Short cache test without shortening the can animation')
    p.add_argument('--out',default='',help='Suffix for the saved blend name; keeps canonical deliverables safe')
    p.add_argument('--force',action='store_true',help='Allow overwriting an existing canonical blend')
    p.add_argument('--condensation',action='store_true',help='Add water beads outside cinematic mode')
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=str(path),check_existing=False)

def main():
    a=args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    s.unit_settings.system='METRIC'
    s.unit_settings.scale_length=1
    s.unit_settings.length_unit='MILLIMETERS'
    s.render.threads_mode='FIXED';s.render.threads=8
    s.render.fps=config.SIM['fps']
    mats=materials.build_materials(config.ROOT)
    parts=geometry.build_can({'CAN':config.CAN},mats)
    parts['root']['opening']=a.open
    import liquid_setup
    liquid_setup.build_static({'CAN':config.CAN},mats,parts)
    cameras=studio.build_studio(config)
    if a.mode=='cinematic':
        import cinematic, condensation
        cameras.update(cinematic.build(config, mats, parts))
        condensation.build_condensation(config, mats, parts, plinth=True)
    elif a.condensation:
        import condensation
        condensation.build_condensation(config, mats, parts)
    s.camera=cameras['cine_hero'] if a.mode=='cinematic' else cameras['hero']
    s.cycles.max_bounces=10
    s.cycles.transmission_bounces=8
    s.cycles.adaptive_threshold=.025 if a.final else .06
    s.render.image_settings.color_mode='RGB'
    s.render.image_settings.color_depth='8'
    s['asset']='Monster Mango Loco editable can'
    s['reference_variant']='JUICE 473ml inferred; dimensional envelope from Crown 473ml standard'
    s['artwork_limit']='Front deprojected from reference; unknown rear is blank turquoise. Replace with authorized full-wrap artwork.'
    s['build_script']='scripts/build_project.py'
    if a.mode=='liquid':
        domain,resources=liquid_setup.build_dynamic({'CAN':config.CAN,'SIM':config.SIM},mats,parts)
        import animation
        animation.build_pour_animation({'CAN':config.CAN,'SIM':config.SIM},parts,resources)
        from mathutils import Vector
        for obj in bpy.data.collections['STUDIO'].objects:
            if obj.name.startswith('STUDIO_Pedestal'):obj.hide_render=True;obj.hide_set(True)
            if obj.type=='MESH' and 'Cyclorama' in obj.name:obj.location.z+=.020
        if a.test_frames:
            d=next(m.domain_settings for m in domain.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN')
            d.cache_frame_end=a.test_frames
            d.cache_directory=config.SIM['cache']+'_test'+str(a.test_frames)
        camdata=bpy.data.cameras.new('CAM_Pour');camdata.lens=52;camdata.clip_start=.001
        cam=bpy.data.objects.new('CAM_Pour',camdata);bpy.data.collections['CAMERAS'].objects.link(cam)
        cam.location=(.32,-.49,.26);aim=Vector((0,-.10,.065))
        cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler()
        for obj in bpy.data.collections['STUDIO'].objects:
            if obj.type=='LIGHT':
                obj.location.y-=.06
                obj.rotation_euler=(Vector((0,-.10,.07))-obj.location).to_track_quat('-Z','Y').to_euler()
        s.camera=bpy.data.objects.get('CAM_Pour') or cameras['three_quarter']
    elif a.mode=='master':
        for obj in bpy.data.collections['STUDIO'].objects:
            if obj.type!='LIGHT':obj.hide_render=True;obj.hide_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.clip_start=.001
                area.spaces.active.clip_end=100
                area.spaces.active.region_3d.view_distance=.36
                area.spaces.active.region_3d.view_location=(0,0,config.CAN['height']/2)
    s.frame_set(1)
    import view_defaults
    view_defaults.configure(bpy)
    name='mango_loco_'+a.mode+('_test' if a.test_frames else '')
    if a.out:name+='_'+a.out
    path=config.ROOT/'blender'/(name+'.blend')
    if path.exists() and not (a.out or a.force):
        print('REFUSED_OVERWRITE',path,'pass --out NAME for a dev copy or --force to overwrite',flush=True)
        sys.exit(3)
    save(path)
    if a.bake:
        import bake_liquid
        bake_liquid.bake()
        save(path)
    if a.render:
        s.cycles.samples=config.RENDER['final_samples'] if a.final else config.RENDER['preview_samples']
        size=config.RENDER['final_size'] if a.final else config.RENDER['preview_size']
        for name in a.render.split(','):
            s.camera=cameras[name]
            rec=cameras[name].get('recommended_resolution')
            if a.final and rec:
                s.render.resolution_x,s.render.resolution_y=int(rec[0]),int(rec[1])
            elif name=='cine_wide':
                s.render.resolution_x,s.render.resolution_y=size[0]*4//3,size[0]*3//4
            else:
                s.render.resolution_x=size[0];s.render.resolution_y=size[1] if name!='top' else size[0]
            out=config.ROOT/'renders'/('final' if a.final else 'previews')/(name+('_opened' if a.open else '')+'.png')
            s.render.filepath=str(out)
            bpy.ops.render.render(write_still=True)
            print('RENDER_DONE',out,flush=True)
    s.camera=(cameras['cine_hero'] if a.mode=='cinematic' else cameras['hero']) if a.mode!='liquid' else s.camera
    view_defaults.configure(bpy)
    s.cycles.samples=config.RENDER['final_samples']
    s.render.resolution_x=config.RENDER['final_size'][0];s.render.resolution_y=config.RENDER['final_size'][1]
    save(path)
    print('BUILD_DONE',path,flush=True)

if __name__=='__main__':
    main()
    from batch_utils import finish
    finish()

