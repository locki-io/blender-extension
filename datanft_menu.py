# class invoke to store information from the data NFT of the user 
import bpy
from bpy.props import StringProperty

class NftUrlItem(bpy.types.PropertyGroup):
    identifier: StringProperty(name="Identifier")
    originalUrl: StringProperty(name="Original URL")
    thumbnailUrl: StringProperty(name="Thumbnail URL")
    url: StringProperty(name="URL")
    uri1: StringProperty(name="URI1")
    uri2: StringProperty(name="URL2")

class nft_menu(bpy.types.Menu):
    bl_label = "My MultiversX NFT Menu"
    bl_idname = "OBJECT_MT_nft_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.open_mainfile")
        layout.operator("wm.save_as_mainfile")

def register():
    addon_keymaps = []
    bpy.utils.register_class(nft_menu)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu', 'L', 'PRESS', ctrl=True, shift=True, alt=False)
        kmi.properties.name =  nft_menu.bl_idname
        addon_keymaps.append((km, kmi))

def unregister():
        addon_keymaps = []
        bpy.utils.unregister_class(nft_menu)
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
        addon_keymaps.clear()

# iteration des Urls 
#for item in data:
#        if 'media' in item and item['media']:
#            new_item = scene.nft_url_list.add()
#            new_item.identifier = item['identifier']
#            media = item['media'][0]
#            new_item.originalUrl = media.get('originalUrl', '')
#            new_item.thumbnailUrl = media.get('thumbnailUrl', '')
#            new_item.url = media.get('url', '')
#            uris = item.get('uris', [])
#            if uris:
#                new_item.uri1 = uris[0] if len(uris) > 0 else ''
#                new_item.uri2 = uris[1] if len(uris) > 1 else ''