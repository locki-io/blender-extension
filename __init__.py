# SPDX-License-Identifier: GPL-2.0-or-later

import logging  # from blender cloud addon
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import PointerProperty, BoolProperty, StringProperty, IntProperty, CollectionProperty, EnumProperty
from bpy.types import AddonPreferences, Context, Operator, PropertyGroup
import bpy
import typing
import datetime

bl_info = {
    'name': 'Locki-ID-Addon',
    'author': 'Satish NVRN, Calin Georges, Jean-Noël Schilling',
    'version': (0, 1, 5),
    'blender': (3, 6, 2),
    'location': 'Add-on preferences + navigate to 3D view panel',
    "doc_url": "https://github.com/locki-io/locki_id_addon/",
    'description':
        'Stores your Locki ID credentials(API key) for usage of your stored NFTs',
    'category': 'Development'
}

if 'communication' in locals():
    import importlib

    # noinspection PyUnboundLocalVariable
    communication = importlib.reload(communication)
    # noinspection PyUnboundLocalVariable
    profiles = importlib.reload(profiles)
    get_scripts = importlib.reload(get_scripts)
    clean_scene = importlib.reload(clean_scene)
    mvx_requests = importlib.reload(mvx_requests)
    # datanft_menu = importlib.reload(datanft_menu)
else:
    from . import communication, profiles, get_scripts, clean_scene, mvx_requests

LockiIdProfile = profiles.LockiIdProfile
LockiIdCommError = communication.LockiIdCommError

log = logging.getLogger(__name__)

# note assumption no subclient token but nft_list
__all__ = ('get_active_profile', 'get_active_address', 'create_nft_list',
           'is_logged_in', 'LockiIdProfile', 'LockiIdCommError')


def get_active_address() -> str:
    """Get the id of the currently active profile. If there is no
    active profile on the file, this function will return an empty string.
    """

    return LockiIdProfile.address


def get_active_profile() -> LockiIdProfile:
    """Returns the active Locki ID profile. If there is no
    active profile on the file, this function will return None.

    :rtype: LockiIdProfile
    """

    if not LockiIdProfile.address:
        return None

    return LockiIdProfile


def is_logged_in() -> bool:
    """Returns whether the user is logged in on Locki ID or not."""

    return bool(LockiIdProfile.address != '')


def token_expires() -> typing.Optional[datetime.datetime]:
    """Returns the token expiry timestamp.

    Returns None if the token expiry is unknown. This can happen when
    the last login/validation was performed using a version of this
    add-on that was older than 1.3.
    """

    exp = LockiIdProfile.expires
    if not exp:
        return None

    # Try parsing as different formats. A new Blender ID is coming,
    # which may change the format in which timestamps are sent.
    formats = [
        '%Y-%m-%dT%H:%M:%SZ',  # ISO 8601 with Z-suffix
        '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO 8601 with fractional seconds and Z-suffix
        '%a, %d %b %Y %H:%M:%S GMT',  # RFC 1123, used by old Blender ID
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(exp, fmt)
        except ValueError:
            # Just use the next format string and try again.
            pass

    # Unable to parse, may as well not be there then.
    return None


class LockiIdPreferences(AddonPreferences):
    bl_idname = __name__

    error_message: StringProperty(
        name='Error Message',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    ok_message: StringProperty(
        name='Message',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    address: StringProperty(
        name='wallet address',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    api_key: StringProperty(
        name='API KEY',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='PASSWORD'
    )
    nonce: IntProperty(
        name='nonce', 
        default= 0
    )

    # store the NFTs in addon_prefs 
    # Define a PropertyGroup to represent items in the combobox
    class EnumNftsPropertyGroup(bpy.types.PropertyGroup):
        identifier: bpy.props.StringProperty()
        name: bpy.props.StringProperty()
        url: bpy.props.StringProperty()

    bpy.utils.register_class(EnumNftsPropertyGroup)    
    # Define a CollectionProperty to store items for the combobox
    nfts_collection: bpy.props.CollectionProperty(
        #items=[("default", "default", "Choose your nft")],
        name="My Nfts",
        #default="default",        
        description='All loaded Nfts by identifier',
        type=EnumNftsPropertyGroup
    )

    def reset_messages(self):
        self.ok_message = ''
        self.error_message = ''

    def draw(self, context):
        layout = self.layout

        if self.error_message:
            sub = layout.row()
            sub.alert = True  # labels don't display in red :(
            sub.label(text=self.error_message, icon='ERROR')
        if self.ok_message:
            sub = layout.row()
            sub.label(text=self.ok_message, icon='FILE_TICK')

        active_profile = get_active_profile()
        if active_profile:
            expiry = token_expires()
            now = datetime.datetime.utcnow()

            if expiry is None:
                layout.label(
                    text='We do not know when your token expires, please validate it')
            elif now >= expiry:
                layout.label(text='Your login has expired! Log out and log in again to refresh it',
                             icon='ERROR')
            else:
                time_left = expiry - now
                if time_left.days > 14:
                    exp_str = tip_('on {:%Y-%m-%d}').format(expiry)
                elif time_left.days > 1:
                    exp_str = tip_('in %i days') % time_left.days
                elif time_left.seconds >= 7200:
                    exp_str = tip_('in %i hours') % round(
                        time_left.seconds / 3600)
                elif time_left.seconds >= 120:
                    exp_str = tip_('in %i minutes') % round(
                        time_left.seconds / 60)
                else:
                    exp_str = tip_('within seconds')

                endpoint = communication.auth_endpoint()
                if endpoint == communication.AUTH_ENDPOINT:
                    msg = tip_(
                        'You are logged with key %s') % active_profile.api_key
                else:
                    msg = tip_('You are logged in as %s at %s') % (
                        active_profile.api_key, endpoint)

                col = layout.column(align=True)
                col.label(text=msg, icon='WORLD_DATA')
                if time_left.days < 14:
                    col.label(text=tip_('Your token will expire %s. Please log out and log in again '
                                        'to refresh it') % exp_str, icon='PREVIEW_RANGE')
                else:
                    col.label(text=tip_('Your authentication token expires %s') % exp_str,
                              icon='BLANK1')

            row = layout.row().split(factor=0.8)
            row.operator('locki_id.logout')
            row.operator('locki_id.validate')
            
        else:
            layout.prop(self, 'address')
            layout.prop(self, 'api_key')

            # layout.prop(self, 'api_secret')
            layout.operator('locki_id.login')

class LockiIdMixin:
    @staticmethod
    def addon_prefs(context):
        try:
            prefs = context.preferences
        except AttributeError:
            prefs = context.user_preferences

        addon_prefs = prefs.addons[__name__].preferences
        addon_prefs.reset_messages()
        return addon_prefs

class LockiIdLogin(LockiIdMixin, Operator):
    bl_idname = 'locki_id.login'
    bl_label = 'Login'

    def execute(self, context):
        import random
        import string

        addon_prefs = self.addon_prefs(context)

        auth_result = communication.locki_id_server_authenticate(
            #address=addon_prefs.address,
            api_key=addon_prefs.api_key,
        )

        if auth_result.success:
            # Prevent saving the secret in user preferences. Overwrite the secret with a
            # random string, as just setting to '' might only replace the first byte with 0.
            # !!!! NO API secret !!!
            # pwlen = len(addon_prefs.api_secret)
            # rnd = ''.join(random.choice(string.ascii_uppercase + string.digits)
            #               for _ in range(pwlen + 16))
            # addon_prefs.api_secret = rnd
            # addon_prefs.api_secret = ''
            # JNS add the bearer token, signature, ...
            profiles.save_as_active_profile(
                auth_result,
                addon_prefs.address,
                addon_prefs.api_key,
                {},
                "0",
            )
            addon_prefs.ok_message = tip_('Logged in')
        else:
            addon_prefs.error_message = auth_result.error_message
            if LockiIdProfile.address:
                profiles.logout(LockiIdProfile.address)

        LockiIdProfile.read_json()

        return {'FINISHED'}


class LockiIdValidate(LockiIdMixin, Operator):
    bl_idname = 'locki_id.validate'
    bl_label = 'Validate'

    def execute(self, context):
        addon_prefs = self.addon_prefs(context)

        err = validate_token()
        if err is None:
            addon_prefs.ok_message = tip_('Authentication token is valid')
        else:
            addon_prefs.error_message = tip_(
                '%s; you probably want to log out and log in again') % err

        LockiIdProfile.read_json()

        return {'FINISHED'}

def validate_token() -> typing.Optional[str]:
    """Validates the current user's token with Locki ID.

    Also refreshes the stored token expiry time.

    :returns: None if everything was ok, otherwise returns an error message.
    """

    expires, err = communication.locki_id_server_validate(
        token=LockiIdProfile.token)
    if err is not None:
        return err

    LockiIdProfile.expires = expires
    LockiIdProfile.save_json()

    return None

class LockiIdLogout(LockiIdMixin, Operator):
    bl_idname = 'locki_id.logout'
    bl_label = 'Logout'

    def execute(self, context):
        addon_prefs = self.addon_prefs(context)

        communication.locki_id_server_logout(LockiIdProfile.address,
                                             LockiIdProfile.token)

        profiles.logout(LockiIdProfile.address)
        LockiIdProfile.read_json()

        addon_prefs.ok_message = tip_('You have been logged out')
        return {'FINISHED'}

class UTILS_OT_get_nonce(LockiIdMixin, bpy.types.Operator):
    """Get nonce from MvX address """

    bl_idname = "utils.get_nonce"
    bl_label = "get address nonce"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        addon_prefs = self.addon_prefs(context)
        result = mvx_requests.check_address_nonce(LockiIdProfile.address)

        if result:
            
            LockiIdProfile.nonce = result["nonce"]
            addon_prefs.nonce = result["nonce"]
            LockiIdProfile.save_json()
        mvx_requests.show_message(str(LockiIdProfile.address), f"Nonce: {str(result['nonce'])}")

        LockiIdProfile.read_json()
        return {"FINISHED"}

#def update_enum_nft_identifiers(self, context):
#    addon_prefs = self.addon_prefs(context)
#    updated_identifiers = mvx_requests.transform_nft_urls_in_menu(nft_url=LockiIdProfile.nfts)
#    addon_prefs.nft_identifier.items = updated_identifiers

class UTILS_OT_get_nfts(LockiIdMixin, bpy.types.Operator):
    """Get NFTs from MvX address """

    bl_idname = "utils.get_nfts"
    bl_label = "get urls from nfts"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        addon_prefs = self.addon_prefs(context)

        nft_list = mvx_requests.get_nftlist_from_address(LockiIdProfile.address)
        nft_urls = mvx_requests.get_urllist_from_list(nft_list)

        # store them into the profile 
        LockiIdProfile.nfts = nft_urls
        test = mvx_requests.transform_nft_urls_in_menu(nft_urls)
        # debugging the result : 
        # print(test)
        count = len(test)
        mvx_requests.show_message(LockiIdProfile.address, f"{count} NFTs loaded")
        content_menu_nft = mvx_requests.transform_nft_urls_in_menu(nft_urls)
        print(content_menu_nft)
        LockiIdPreferences.nfts_collection = content_menu_nft
        # nfts_collection is readonly but I would like to do that:
        #addon_prefs.nfts_collection = mvx_requests.transform_nft_urls_in_menu(nft_urls)
        #expect a string enum not a list
        LockiIdProfile.save_json()

        addon_prefs.ok_message = tip_('You have loaded the NFTs')
        LockiIdProfile.read_json()

        return {"FINISHED"}

# class naming convention ‘CATEGORY_PT_name’
class VIEW3D_PT_locki_panel(LockiIdMixin, bpy.types.Panel):
    bl_idname = "view3d.locki_panel"
    # where to add the panel in the UI
    # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_space_type = "VIEW_3D"
    # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)
    bl_region_type = "UI"
    # add labels
    bl_category = "Locki.io"  # found in the Sidebar
    bl_label = "Locki Panel"  # found at the top of the Panel

    # ui_expanded_nft: BoolProperty(
    #     name="Show Nfts Expanded",
    #     description="Shows the box 'NFT' expanded in user interface",
    #     default=False, options={'SKIP_SAVE'})

    def prepare(self, context):        
        sce = context.scene
        self.recall_mode = context.object.mode

    def draw(self, context):
        """define the scene of the panel"""
        locki = context.scene.locki
        """define the layout of the panel"""
        layout = self.layout
        # print('is logged :' + str(is_logged_in()))
        if is_logged_in():
            row = layout.row()
            row.operator("utils.get_nonce", text="Check MvX nonce")
            row = layout.row()
            row.operator("utils.get_nfts", text="Get MvX nfts")

            # Access the items in AddonPreferences and populate the combobox
            #preferences = context.preferences.addons[__name__].preferences
            # or 
            addon_prefs = self.addon_prefs(context)
            nfts_collection = addon_prefs.nfts_collection

            # Create a list of tuples for the items in the combobox
            items = [("default", "Default", "Choose your nft")]  # Default item

            # Add items based on your nfts_collection
            for items in nfts_collection:
                items.append((items.identifier, items.description, items.url))  # Use the data from your collection
            
            
            # Display the combobox
            box = layout.box()
            row = box.row(align=True)
            row.label(text='My NFTs')
            row.prop(locki, "ui_expanded_nft", text="Select an nft:", 
                              icon=('TRIA_DOWN' if locki.ui_expanded_nft else 'TRIA_RIGHT'))
            if locki.ui_expanded_nft:
                box.prop(locki,"", text="my NFTs")
            row = box.row(align=True)
            row.prop(locki, "file_format")
            row = box.row(align=True)
            row.prop(locki, "my_selected_nft", text="Selection")
 
            # Use your scene property ??? really 
            
        row = self.layout.row()
        row.operator("mesh.clean_scene", text="Clear Scene")
        self.layout.separator()
        row = self.layout.row()
        row.operator("mesh.primitive_cube_add", text="Add Cube")
        row = self.layout.row()
        row.operator("mesh.primitive_ico_sphere_add", text="Add Ico Sphere")
        row = self.layout.row()
        row.operator("object.shade_smooth", text="Shade Smooth")

        self.layout.separator()

        row = self.layout.row()
        row.operator("mesh.add_subdiv_monkey", text="Add Subdivided Monkey")
        row = self.layout.row()
        row.operator("mesh.add_rotating_cube", text="Add rotating cube")

class SceneProperties(PropertyGroup):
    file_format: EnumProperty(
        name="Filter",
        description="The file format of your NFT",
        items=(
            ('SVG', "SVG", ""),
            ('PY', "PY", ""),
            ('GTLB', "GTLB", ""),
            ('PNG', "PNG", ""),
        ),
        default='SVG',
    )
    ui_expanded_nft: BoolProperty(
        name="Show Nfts Expanded",
        description="Shows the box 'Nfts choice' expanded in user interface",
        default=True, options={'SKIP_SAVE'})
    
    # Define your custom property for the Scene object
    my_selected_nft: StringProperty(
        name="My Selected Nft",
        default="",
        description="A description for my selected NFT"
    )

module_classes = (
    SceneProperties,

    LockiIdLogin,
    LockiIdLogout,
    LockiIdPreferences,
    LockiIdValidate,

    UTILS_OT_get_nfts, # register utility operators
    UTILS_OT_get_nonce, # Register utility operators

    get_scripts.MESH_OT_add_subdiv_monkey, # Register mesh and scene utilities
    get_scripts.MESH_OT_add_rotating_cube_obj, # Register mesh and scene utilities
    clean_scene.MESH_OT_clean_scene, # Register mesh and scene utilities

    VIEW3D_PT_locki_panel, # register panel    
)


def register():
    # Register profile and data-related functionalities
    profiles.register()

    for cls in module_classes:
        bpy.utils.register_class(cls)

    # Define a full scene (UI) reserved for the addon all defined in Class Scene property
    bpy.types.Scene.locki = PointerProperty(type=SceneProperties)
   
    LockiIdProfile.read_json()

    # Reset messages or any final initialization
    preferences = LockiIdMixin.addon_prefs(bpy.context)
    preferences.reset_messages()


def unregister():
    # Reset messages or any final de-initialization
    preferences = LockiIdMixin.addon_prefs(bpy.context)
    preferences.reset_messages()  # Assuming you might want to clean up some stuff during unregister as well.
    
    # Unregister Classes in reverse order
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()
