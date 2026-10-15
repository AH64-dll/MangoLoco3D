"""Run only after the baked action frames have been rendered and visually reviewed."""
import sys,json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
project=Path(bpy.data.filepath).parent.parent
report=json.loads((project/'reports'/'validation_mango_loco_liquid.json').read_text())
assert not report['errors'],'Cannot finalize a failed physics validation'
assert 'pour_verified_v4' in report['fluid']['cache'],'Validation belongs to another bake'
domain=bpy.data.objects['SIM_Liquid_Domain']
d=next(m.domain_settings for m in domain.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN')
assert d.has_cache_baked_data and d.has_cache_baked_mesh
domain.display_type='TEXTURED'
domain['simulation_status']='64-frame data and surface baked; supervisor inspected action frames. See reports/qa_report.md for limits.'
bpy.context.scene.frame_set(64)
import view_defaults
view_defaults.configure(bpy)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('PHYSICS_DELIVERY_FINALIZED',flush=True)
from batch_utils import finish
finish()
