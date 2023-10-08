import bpy

# Define a PropertyGroup to structure the data stored in AddonPreferences
class MyAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    # Define a PropertyGroup to represent items in the combobox
    class EnumNftsPropertyGroup(bpy.types.PropertyGroup):
        identifier: bpy.props.StringProperty()
        name: bpy.props.StringProperty()
        url: bpy.props.StringProperty()

    # Define a CollectionProperty to store nfts for the combobox
    nfts_collection: bpy.props.CollectionProperty(
        items=[("default", "default", "Choose your nft")],
        name="My Nfts",
        default="default",        
        description='All loaded Nfts by identifier',
        type=EnumNftsPropertyGroup
    )

# Define an Operator to update the nfts in the CollectionProperty
class UpdateNftsOperator(bpy.types.Operator):
    bl_idname = "my.update_nfts_operator"
    bl_label = "Update Nfts"

    def execute(self, context):
        # Dynamic logic to update items in the CollectionProperty
        addon_prefs = self.addon_prefs(context)



# Define a Panel to display the combobox
class MyPanel(bpy.types.Panel):
    bl_idname = "my.panel"
    bl_label = "My Panel"
    bl_category = "My Addon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        # Access the items in AddonPreferences and populate the combobox
        preferences = context.preferences.addons[__name__].preferences
        nfts_collection = preferences.nfts_collection
        
        # Create a list of tuples for the items in the combobox
        items = [("default", "Default", "Choose your nft")]  # Default item

        # Add items based on your nfts_collection
        for items in nfts_collection:
            items.append((items.identifier, items.description, items.url))  # Use the data from your collection

        # Display the combobox
        layout.label(text="Select an item:")
        layout.prop(context.scene, "my_selected_item", text="NFT Items", icon='QUESTION')  # Use your scene property

def register():
    bpy.utils.register_class(MyAddonPreferences)
    bpy.utils.register_class(UpdateNftsOperator)
    bpy.utils.register_class(EnumNftsPropertyGroup)
    bpy.utils.register_class(MyPanel)

def unregister():
    bpy.utils.unregister_class(MyAddonPreferences)
    bpy.utils.unregister_class(UpdateNftsOperator)
    bpy.utils.unregister_class(EnumNftsPropertyGroup)
    bpy.utils.unregister_class(MyPanel)


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

def default_items (self, context):
    items=(
            ('default', "", "Choose your nft"),
            ('OPTION1', "Option 1", "Description 1"),
            ('OPTION2', "Option 2", "Description 2"),
    )
    return items

#def update_enum_nft(self, context):
#    self.enum_nft = update_enum_nft(self, context)

# def update_enum_nft(self, context):
#     items = (('default', "", "Choose your nft"))
    
#     #nfts = LockiIdProfile.nfts
#     if not nfts:  # Check if nfts is None or an empty dictionary
#         return items 
    
#     for identifier, data in nfts.items():
#         for url in data.items():
#             ext = url.split('.')[-1]  # Get the file extension
#             option_id = f"{identifier}_{ext.upper()}"
#             option_name = f"{identifier} ({ext})"
#             items.append((option_id, option_name, url))

#     return items

# class enum_mynfts_properties(bpy.types.PropertyGroup):
#     enum_nft : bpy.props.EnumProperty(
#         items=default_items,
#         #update=update_enum_nft,
#         name= "Enum Nfts",
#         default = "default",
#     )


    
    