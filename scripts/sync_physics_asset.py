"""Update only visible can geometry/art after a bake; retain solver boundaries and cache."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import config,geometry,materials
root=bpy.data.objects['CAN_Rig']
old=set()
for name in ['CAN_GEOMETRY','CAN_DETAILS','CAN_SOURCE']:
    col=bpy.data.collections.get(name)
    if col:old.update(o for o in col.objects if o!=root)
oldcoll=bpy.data.objects.get('SIM_Can_Collider')
if oldcoll:old.add(oldcoll)
mats=materials.build_materials(config.ROOT)
parts=geometry.build_can({'CAN':config.CAN},mats)
newroot=parts['root']
newobjects=set()
for name in ['CAN_GEOMETRY','CAN_DETAILS','CAN_SOURCE','SIMULATION']:
    newobjects.update(o for o in bpy.data.collections[name].objects if o not in old and o not in (root,newroot))
for obj in newobjects:
    if obj.parent==newroot:obj.parent=root
    if obj.animation_data:
        for curve in obj.animation_data.drivers:
            for var in curve.driver.variables:
                for target in var.targets:
                    if target.id==newroot:target.id=root
for obj in old:bpy.data.objects.remove(obj,do_unlink=True)
bpy.data.objects.remove(newroot,do_unlink=True)
for obj in list(newobjects):
    if obj.name.startswith(('CAN_','SIM_Can_Collider')) and obj.name.endswith('.001'):obj.name=obj.name[:-4]
bpy.context.scene.frame_set(1);root.update_tag();bpy.context.view_layer.update()
domain=bpy.data.objects['SIM_Liquid_Domain']
d=next(m.domain_settings for m in domain.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN')
assert d.has_cache_baked_data and d.has_cache_baked_mesh,'Cache was not retained'
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('PHYSICS_ASSET_SYNC_DONE; solver cache retained',flush=True)
from batch_utils import finish
finish()
