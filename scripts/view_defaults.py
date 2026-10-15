"""Make an editable scene open on its camera with the useful rig selected."""
def configure(bpy):
    root=bpy.data.objects.get('CAN_Rig')
    if root:
        bpy.ops.object.select_all(action='DESELECT')
        root.hide_set(False);root.select_set(True)
        bpy.context.view_layer.objects.active=root
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.clip_start=.001;space.clip_end=100
                space.region_3d.view_perspective='CAMERA'
                space.shading.type='MATERIAL'
                space.shading.use_scene_lights=True
                space.shading.use_scene_world=True

if __name__=='__main__':
    import sys
    from pathlib import Path
    import bpy
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    configure(bpy)
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    from batch_utils import finish
    finish()
