"""Inspect actual saved assets, mechanisms, UVs and cached liquid geometry."""
import sys,json,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector

def inspect():
    scene=bpy.context.scene
    report={'file':Path(bpy.data.filepath).name,'blender':bpy.app.version_string,'objects':{},'errors':[]}
    for name in ['CAN_Rig','CAN_Body','CAN_Bottom_Dome','CAN_Lid','CAN_Pull_Tab','CAN_Scored_Panel','LIQ_Static_Fill']:
        if name not in bpy.data.objects:report['errors'].append('Missing object '+name)
    for name in ['CAN_GEOMETRY','CAN_DETAILS','LIQUID_STATIC','STUDIO','CAMERAS','SIMULATION']:
        if name not in bpy.data.collections:report['errors'].append('Missing collection '+name)
    report['textures']=[{'name':im.name,'packed':bool(im.packed_file),'path':im.filepath,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE']
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file():report['errors'].append('Missing image '+im.name)
    for obj in bpy.data.objects:
        if obj.type!='MESH' or not obj.name.startswith(('CAN_','SIM_','LIQ_')):continue
        bm=bmesh.new();bm.from_mesh(obj.data)
        nonmanifold=sum(not e.is_manifold for e in bm.edges)
        volume=bm.calc_volume(signed=True)
        bm.free()
        d={'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons),'nonmanifold_edges':nonmanifold,'signed_volume_m3':volume,'dimensions_m':list(obj.dimensions),'modifiers':[(m.name,m.type) for m in obj.modifiers],'parent':obj.parent.name if obj.parent else None}
        report['objects'][obj.name]=d
        if obj.name.startswith('CAN_') and nonmanifold:report['errors'].append(obj.name+' nonmanifold edges '+str(nonmanifold))
    body=bpy.data.objects['CAN_Body'];uv=body.data.uv_layers.active
    if not uv:report['errors'].append('Body missing UV layer')
    else:
        maxspan=max(max(uv.data[i].uv.x for i in p.loop_indices)-min(uv.data[i].uv.x for i in p.loop_indices) for p in body.data.polygons if p.material_index==1)
        report['max_face_u_span']=maxspan
        if maxspan>.02:report['errors'].append('UV seam crosses whole label')
    root=bpy.data.objects['CAN_Rig'];opening=float(root['opening'])
    opening_evidence=[]
    # Ray through a point near the outer end of the scored panel: blocked at
    # rest, clear after the panel rotates into the can. Test actual evaluated mesh.
    for value in [0.,1.]:
        root['opening']=value;root.update_tag();bpy.context.view_layer.update()
        dep=bpy.context.evaluated_depsgraph_get()
        panel=bpy.data.objects['CAN_Scored_Panel'].evaluated_get(dep)
        lid=bpy.data.objects['CAN_Lid'].evaluated_get(dep)
        origin=Vector((0,-.015,.18));direction=Vector((0,0,-1))
        hit_panel=panel.ray_cast(panel.matrix_world.inverted()@origin,panel.matrix_world.to_3x3().inverted()@direction)[0]
        hit_lid=lid.ray_cast(lid.matrix_world.inverted()@origin,lid.matrix_world.to_3x3().inverted()@direction)[0]
        opening_evidence.append({'opening':value,'panel_ray_hit':hit_panel,'lid_ray_hit':hit_lid,'panel_angle':panel.rotation_euler.x,'tab_angle':bpy.data.objects['CAN_Pull_Tab'].evaluated_get(dep).rotation_euler.x})
    root['opening']=opening;root.update_tag();bpy.context.view_layer.update()
    report['opening_test']=opening_evidence
    if not root.animation_data or not root.animation_data.action:
        if not opening_evidence[0]['panel_ray_hit'] or opening_evidence[1]['panel_ray_hit'] or opening_evidence[1]['lid_ray_hit']:report['errors'].append('Opening mechanism failed aperture ray test')
    static=bpy.data.objects['LIQ_Static_Fill'];oldfill=float(root['fill_level'])
    levels=[]
    for fill in [.2,.8]:
        root['fill_level']=fill;root.update_tag();bpy.context.view_layer.update()
        mesh=static.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        levels.append({'fill':fill,'top_z':max(v.co.z for v in mesh.vertices)})
        static.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    root['fill_level']=oldfill
    report['fill_test']=levels
    if levels[1]['top_z']<=levels[0]['top_z']:report['errors'].append('Fill-level control failed')
    domain=bpy.data.objects.get('SIM_Liquid_Domain')
    if domain:
        d=next(m.domain_settings for m in domain.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN')
        report['fluid']={'data_baked':d.has_cache_baked_data,'mesh_baked':d.has_cache_baked_mesh,'cache':d.cache_directory,'cache_exists':Path(bpy.path.abspath(d.cache_directory)).is_dir(),'frames':[]}
        if not (d.has_cache_baked_data and d.has_cache_baked_mesh):report['errors'].append('Liquid data and mesh are not both baked')
        if not report['fluid']['cache_exists']:report['errors'].append('Liquid cache directory is missing')
        for frame in [1,8,20,32,44,56,64]:
            if frame>d.cache_frame_end:continue
            scene.frame_set(frame)
            ob=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh()
            pts=[ob.matrix_world@v.co for v in mesh.vertices]
            local=[root.matrix_world.inverted()@p for p in pts]
            outside=sum(math.hypot(p.x,p.y)>.0335 and p.z<.135 for p in local)
            receiver=bpy.data.objects['SIM_Receiver_Bowl_Proxy'].location
            in_bowl=sum(math.hypot(p.x-receiver.x,p.y-receiver.y)<.04 and 0<=p.z<.032 for p in pts)
            report['fluid']['frames'].append({'frame':frame,'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'outside_lower_can_vertices':outside,'receiver_vertices':in_bowl,'bounds':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)] if pts else None})
            if frame<=8 and outside:report['errors'].append('Liquid visible outside upright can at frame '+str(frame))
            if len(mesh.vertices)<100:report['errors'].append('Empty or unexpectedly small liquid surface at frame '+str(frame))
            ob.to_mesh_clear()
        if d.cache_frame_end>=64 and not any(f['receiver_vertices']>0 for f in report['fluid']['frames'] if f['frame']>=32):
            report['errors'].append('Pour never reaches the receiver in inspected frames')
    target=Path(bpy.data.filepath).parent.parent/'reports'/('validation_'+Path(bpy.data.filepath).stem+'.json')
    target.write_text(json.dumps(report,indent=2))
    print(json.dumps({'report':str(target),'errors':report['errors'],'fluid':report.get('fluid')},indent=2),flush=True)
    if report['errors']:raise RuntimeError('Asset validation errors; see report')

if __name__=='__main__':
    inspect()
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from batch_utils import finish
    finish()

