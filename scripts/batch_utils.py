"""Finish a verified batch without the sandbox's PulseAudio shutdown deadlock."""
def finish():
    import bpy, os, sys
    if bpy.app.background:
        # Call only after explicit saves/renders/report writes have completed.
        # The host blocks PulseAudio IPC and Blender otherwise hangs at exit.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

