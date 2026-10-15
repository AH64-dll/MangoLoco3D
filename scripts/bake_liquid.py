"""Bake a saved physics scene in sequence. Data and mesh must both finish."""
import bpy, time, json
from pathlib import Path

def bake():
    obj=bpy.data.objects.get('SIM_Liquid_Domain') or next(o for o in bpy.data.objects if any(m.type=='FLUID' and m.fluid_type=='DOMAIN' for m in o.modifiers))
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    d=next(m.domain_settings for m in obj.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN')
    bpy.context.scene.frame_set(d.cache_frame_start)
    Path(bpy.path.abspath(d.cache_directory)).mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    print('BAKE_DATA_START',d.cache_directory,flush=True)
    result=bpy.ops.fluid.bake_data()
    print('BAKE_DATA_FINISHED',result,d.has_cache_baked_data,time.monotonic()-start,flush=True)
    if 'FINISHED' not in result or not d.has_cache_baked_data:raise RuntimeError('Liquid data bake failed')
    result=bpy.ops.fluid.bake_mesh()
    print('BAKE_MESH_FINISHED',result,d.has_cache_baked_mesh,time.monotonic()-start,flush=True)
    if 'FINISHED' not in result or not d.has_cache_baked_mesh:raise RuntimeError('Liquid mesh bake failed')
    obj.display_type='TEXTURED'
    obj['simulation_status']='Data and surface baked; inspect rendered frames before visual approval'
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    report={'data_baked':d.has_cache_baked_data,'mesh_baked':d.has_cache_baked_mesh,'elapsed_seconds':time.monotonic()-start,'resolution':d.resolution_max,'frame_start':d.cache_frame_start,'frame_end':d.cache_frame_end,'cache':d.cache_directory}
    (Path(bpy.data.filepath).parent.parent/'reports'/'bake_result.json').write_text(json.dumps(report,indent=2))
    (Path(bpy.data.filepath).parent.parent/'reports'/('bake_result_'+Path(bpy.data.filepath).stem+'.json')).write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    bake()
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from batch_utils import finish
    finish()
