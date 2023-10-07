import bpy

class MESH_OT_open_media_originalUrl(bpy.types.Operator):
    bl_idname = "mesh.open_media_originalUrl"
    bl_label = "Open Original Url from " + OBJECT_MT_nft_menu
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        # import addon_utils
        # addon_utils.load_scripts(*, reload_scripts=True, refresh_scripts=True)
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
        main()
        return {"FINISHED"}