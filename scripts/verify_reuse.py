"""Append only asset collections into an empty scene and inspect dependency portability."""
import sys,json,math
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import config,animation
master=config.ROOT/'blender'/'mango_loco_master.blend'
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(master),link=False) as (src,dst):
    dst.collections=['CAN_GEOMETRY','CAN_DETAILS','LIQUID_STATIC']
for col in dst.collections:bpy.context.scene.collection.children.link(col)
root=bpy.data.objects['CAN_Rig']
root['opening']=1.;root['fill_level']=.5;root.update_tag();bpy.context.view_layer.update()
images=[im for im in bpy.data.images if im.source=='FILE']
assert images and all(im.packed_file for im in images),'Unpacked dependency'
assert bpy.data.objects['CAN_Scored_Panel'].evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler.x>.8,'Opening lost on append'
animation.build_turntable(root)
bpy.context.scene.frame_set(31)
assert math.isclose(root.rotation_euler.z,math.pi/2,abs_tol=.001),'Turntable does not play'
report={'master':str(master.name),'appended_collections':[c.name for c in dst.collections], 'objects':len(bpy.data.objects),'packed_textures':[im.name for im in images],'opening_drives_panel':True,'turntable_frame31_degrees':math.degrees(root.rotation_euler.z),'result':'PASS'}
(config.ROOT/'reports'/'reuse_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
from batch_utils import finish
finish()
