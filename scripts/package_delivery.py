"""Archive the validated deliverables; exclude intermediate bakes and backups."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'README.md']
files.extend(p for p in (ROOT/'assets').rglob('*') if p.is_file())
files.extend((ROOT/'scripts').glob('*.py'))
files.append(ROOT/'scripts'/'run_blender.sh')
files.extend(ROOT/'blender'/('mango_loco_'+mode+'.blend') for mode in ['master','studio','liquid'])
files.extend(p for p in (ROOT/'cache'/'liquid'/'pour_verified_v4').rglob('*') if p.is_file())
files.extend((ROOT/'renders'/'previews').glob('*.png'))
files.extend(p for p in (ROOT/'renders'/'final').rglob('*') if p.is_file())
for name in ['qa_report.md','artwork_sources.md','production_brief.md','geometry_notes.md',
             'studio_notes.md','fluid_notes.md','implementation_plan.md','physics_preflight.json',
             'reuse_verification.json','bake_result_mango_loco_liquid.json',
             'validation_mango_loco_master.json','validation_mango_loco_studio.json',
             'validation_mango_loco_liquid.json','video_metadata.json']:
    files.append(ROOT/'reports'/name)
for mode in ['master','studio','liquid']:
    report=json.loads((ROOT/'reports'/('validation_mango_loco_'+mode+'.json')).read_text())
    assert not report['errors'],mode+' validation errors'
physics=json.loads((ROOT/'reports'/'validation_mango_loco_liquid.json').read_text())['fluid']
assert physics['data_baked'] and physics['mesh_baked']
assert 'pour_verified_v4' in physics['cache'],'Outdated physics validation'
manifest={'status':'Validated delivery','files':[]}
for path in sorted(set(files)):
    data=path.read_bytes()
    manifest['files'].append({'path':str(path.relative_to(ROOT)), 'bytes':len(data),
                              'sha256':hashlib.sha256(data).hexdigest()})
mp=ROOT/'reports'/'delivery_manifest.json'
mp.write_text(json.dumps(manifest,indent=2));files.append(mp)
target=ROOT.parent/'MangoLoco3D.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
    for path in sorted(set(files)):archive.write(path,path.relative_to(ROOT.parent))
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None,'Archive CRC failure'
print(json.dumps({'archive':str(target),'bytes':target.stat().st_size,'files':len(files),'integrity':'PASS'},indent=2))
