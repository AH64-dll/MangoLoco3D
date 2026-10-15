"""Render existing saved scene without rebuilding or rebaking."""
import sys,argparse
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--cameras',default='hero');p.add_argument('--frames',default='');p.add_argument('--samples',type=int,default=32);p.add_argument('--width',type=int,default=720);p.add_argument('--height',type=int,default=900);p.add_argument('--open',type=float,default=-1);p.add_argument('--out',default='previews');p.add_argument('--device',default='auto',choices=['auto','cpu','gpu'])
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

def set_device(scene,want):
    """OptiX, then CUDA, then CPU. A saved scene may carry a GPU device flag
    from a machine that had one; this resolves the actual hardware again."""
    addon=bpy.context.preferences.addons.get('cycles')
    if addon is not None and want!='cpu':
        try:addon.preferences.refresh_devices()
        except Exception:pass
        for backend in ('OPTIX','CUDA'):
            try:
                addon.preferences.compute_device_type=backend
                addon.preferences.refresh_devices()
            except Exception:continue
            devices=[d for d in addon.preferences.devices if d.type==backend]
            if devices:
                for d in addon.preferences.devices:d.use=(d.type==backend)
                scene.cycles.device='GPU'
                scene.cycles.denoiser='OPTIX' if backend=='OPTIX' else 'OPENIMAGEDENOISE'
                return backend
        if want=='gpu':print('GPU requested but no backend found; using CPU',flush=True)
    scene.cycles.device='CPU'
    scene.cycles.denoiser='OPENIMAGEDENOISE'
    return 'CPU'

s=bpy.context.scene;root=Path(bpy.data.filepath).parent.parent
(root/'renders'/a.out).mkdir(parents=True,exist_ok=True)
s.render.engine='CYCLES'
print('RENDER_DEVICE',set_device(s,a.device),flush=True)
s.cycles.samples=a.samples;s.cycles.use_denoising=True
s.render.threads_mode='FIXED';s.render.threads=8
s.render.resolution_x=a.width;s.render.resolution_y=a.height;s.render.resolution_percentage=100
names={'hero':'CAM_Hero','front':'CAM_Front','three_quarter':'CAM_Three_Quarter','side':'CAM_Side','top':'CAM_Top_Detail','pour':'CAM_Pour',
       'cine_hero':'CAM_Cine_Hero','cine_macro':'CAM_Cine_Macro','cine_wide':'CAM_Cine_Wide','cine_top':'CAM_Cine_Top'}
if a.open>=0:
    bpy.data.objects['CAN_Rig']['opening']=a.open;bpy.data.objects['CAN_Rig'].update_tag()
if ':' in a.frames:
    first,last=map(int,a.frames.split(':'))
    frames=range(first,last+1)
else:
    frames=[int(f) for f in a.frames.split(',')] if a.frames else [1]
for frame in frames:
    s.frame_set(frame)
    for camera in a.cameras.split(','):
        s.camera=bpy.data.objects[names[camera]]
        s.render.resolution_y=a.width if camera in ('top','cine_top') else a.height
        suffix=f'_{frame:03}' if a.frames else ('_opened' if a.open==1 else '')
        s.render.filepath=str(root/'renders'/a.out/(camera+suffix+'.png'))
        bpy.ops.render.render(write_still=True)
        print('RENDER_DONE',s.render.filepath,flush=True)

sys.path.insert(0,str(Path(__file__).resolve().parent))
from batch_utils import finish
finish()
