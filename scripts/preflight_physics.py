"""Check the real animated can fits the domain and its spout clears the bowl."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
root=bpy.data.objects['CAN_Rig']
domain=bpy.data.objects['SIM_Liquid_Domain']
corners=[domain.matrix_world@Vector(p) for p in domain.bound_box]
lower=[min(p[i] for p in corners) for i in range(3)]
upper=[max(p[i] for p in corners) for i in range(3)]
errors=[]
for frame in range(1,65):
    bpy.context.scene.frame_set(frame)
    for name in ['CAN_Body','CAN_Bottom_Dome','CAN_Lid','CAN_Pull_Tab']:
        obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
        for p in obj.bound_box:
            world=obj.matrix_world@Vector(p)
            if any(world[i]<lower[i] or world[i]>upper[i] for i in range(3)):
                errors.append(f'{name} outside domain at {frame}')
bpy.context.scene.frame_set(33)
lid=bpy.data.objects['CAN_Lid']
top=max((lid.matrix_local@v.co).z for v in lid.data.vertices)
spout=root.matrix_world@Vector((0,-.0105,top))
bowl=bpy.data.objects['SIM_Receiver_Bowl_Proxy']
bowl_top=max((bowl.matrix_world@v.co).z for v in bowl.data.vertices)
clearance=spout.z-bowl_top
if clearance<.024:errors.append('Spout less than 24 mm above receiver')
report={'domain_bounds_m':[lower,upper],'can_within_domain_all_64_frames':not errors,
        'spout_world_m':list(spout),'spout_clearance_above_bowl_m':clearance,'errors':errors}
(Path(bpy.data.filepath).parent.parent/'reports'/'physics_preflight.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
if errors:raise RuntimeError('Physics preflight failed')
from batch_utils import finish
finish()
