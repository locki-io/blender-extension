# SPDX-License-Identifier: GPL-2.0-or-later

import logging  # from blender cloud addon
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import PointerProperty, StringProperty
from bpy.types import AddonPreferences, Context, Operator, PropertyGroup
import bpy
import typing
import datetime


bl_info = {
    'name': 'Locki-ID-Addon',
    'author': 'Jean-Noël Schilling',
    'version': (0, 1, 2),
    'blender': (3, 6, 2),
    'location': 'Add-on preferences',
    'description':
        'Stores your Locki ID credentials(API key-secret) for usage of your stored NFT',
    'category': 'System'
}


if 'communication' in locals():
    import importlib

    # noinspection PyUnboundLocalVariable
    communication = importlib.reload(communication)
    # noinspection PyUnboundLocalVariable
    profiles = importlib.reload(profiles)
    get_scripts = importlib.reload(get_scripts)
    clean_scene = importlib.reload(clean_scene)
    datanft_menu = importlib.reload(datanft_menu)
else:
    from . import communication, profiles, get_scripts, clean_scene, datanft_menu
LockiIdProfile = profiles.LockiIdProfile
LockiIdCommError = communication.LockiIdCommError

log = logging.getLogger(__name__)

# note assumption no subclient token but nft_list
__all__ = ('get_active_profile', 'get_active_address', 'create_nft_list',
           'is_logged_in', 'LockiIdProfile', 'LockiIdCommError')

# Public API functions

# in blender userid is an UUID associated to the user, but on MVX we use the bech32


def get_valid_profile() -> LockiIdProfile:
    """Verify if the address is valid. If there is a address in active profile 
    instead of an API KEY, this function will return true.
    """
    if not LockiIdProfile.address:
        return None 
    
    return LockiIdProfile

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

    if not LockiIdProfile.api_key:
        return None

    return LockiIdProfile


def is_logged_in() -> bool:
    """Returns whether the user is logged in on Locki ID or not."""

    return bool(LockiIdProfile.address)

def create_nft_urls(address: str, webservice_endpoint: str) -> dict:
    """Lets the address create a NFT list in the profile.

    :param address: the address of the wallet
    :param end point the mvx endpoint .
    :returns: the list of NFTs (with urls and other required info)
    :raises: locki_id.communication.LockiIdCommError when the nft list is not provided.
    """

    # Communication between us and MvX.
    profile = get_valid_profile()
    mvx_info = communication.get_urllist_from_list(address, webservice_endpoint)
    nft_identifier = mvx_info['identifier']

    # Send the token to the webservice.
    #user_id = communication.send_token_to_subclient(webservice_endpoint, profile.user_id,
    #                                                subclient_token, subclient_id)

    # Now that everything is okay we can store the token locally.
    profile.nfts[address] = {'nft': nft_identifier}
    profile.save_json()

    return mvx_info

def get_nfts_of_user(address: str) -> str:
    """Returns the nfts from the user.

    Requires that the user has been authenticated at the subclient using
    a call to create_subclient_token(...)

    :returns: the subclient-local user ID, or the empty string if not logged in.
    """

    if not LockiIdProfile.address:
        return ''

    return LockiIdProfile.nfts[address]['identifier']

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
    # api_secret: StringProperty(
    #     name='API SECRET',
    #     default='',
    #     options={'HIDDEN', 'SKIP_SAVE'},
    #     subtype='PASSWORD'  # JNS check whether there is a special time for that
    # )

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
        valid_profile = get_valid_profile()
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

                endpoint = communication.locki_id_endpoint()
                if endpoint == communication.LOCKI_ID_ENDPOINT:
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
        elif valid_profile:
            msg = tip_('Your address is %s') % valid_profile.address

            layout.prop(self, 'api_key')
            # layout.prop(self, 'api_secret')
            layout.operator('locki_id.login')
            
        else:
            layout.prop(self, 'address')
            layout.operator('address_check.login')

            layout.prop(self, 'api_key')
            # layout.prop(self, 'api_secret')
            layout.operator('locki_id.login')

# JNS : test the Mixin
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

class AddressCheckLogin(LockiIdMixin, Operator):
    bl_idname = 'address_check.login'
    bl_label = 'Check address'

    def execute(self, context):
        addon_prefs = self.addon_prefs(context)

        auth_result = communication.mvx_authenticate(
            address=addon_prefs.address
        )
        if auth_result.success:
            profiles.save_as_valid_address_profile(
                auth_result,
                addon_prefs.address,
                {}
            )
            addon_prefs.ok_message = tip_('address ok')
        else:
            addon_prefs.error_message = auth_result.error_message
            if LockiIdProfile.address:
                profiles.logout(LockiIdProfile.address)

        LockiIdProfile.read_json()
        
        return {'FINISHED'}       

class LockiIdLogin(LockiIdMixin, Operator):
    bl_idname = 'locki_id.login'
    bl_label = 'Login'

    def execute(self, context):
        import random
        import string

        addon_prefs = self.addon_prefs(context)

        auth_result = communication.locki_id_server_authenticate(
            address=addon_prefs.address,
            api_key=addon_prefs.api_key,
        )

        if auth_result.success:
            # Prevent saving the secret in user preferences. Overwrite the secret with a
            # random string, as just setting to '' might only replace the first byte with 0.
            pwlen = len(addon_prefs.api_secret)
            rnd = ''.join(random.choice(string.ascii_uppercase + string.digits)
                          for _ in range(pwlen + 16))
            addon_prefs.api_secret = rnd
            addon_prefs.api_secret = ''
            # JNS add the bearer token, signature, ...
            profiles.save_as_active_profile(
                auth_result,
                addon_prefs.address, 
                {}
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


# class naming convention ‘CATEGORY_PT_name’
class VIEW3D_PT_locki_panel(bpy.types.Panel):

    # where to add the panel in the UI
    # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_space_type = "VIEW_3D"
    # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)
    bl_region_type = "UI"

    # add labels
    bl_category = "Locki category"  # found in the Sidebar
    bl_label = "Locki Panel"  # found at the top of the Panel

    def draw(self, context):
        """define the layout of the panel"""

        row = self.layout.row()
        row.operator("utils.get_nonce", text="Check MvX nonce")
        row = self.layout.row()
        row.operator("utils.get_nfts", text="Get MvX nfts")
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


def register():
    profiles.register()
    LockiIdProfile.read_json()

    bpy.utils.register_class(LockiIdLogin)
    bpy.utils.register_class(LockiIdLogout)
    bpy.utils.register_class(LockiIdPreferences)
    bpy.utils.register_class(LockiIdValidate)
    bpy.utils.register_class(AddressCheckLogin)
    
    # register panel 
    bpy.utils.register_class(VIEW3D_PT_locki_panel)
    bpy.utils.register_class(get_scripts.MESH_OT_add_subdiv_monkey)
    bpy.utils.register_class(get_scripts.MESH_OT_add_rotating_cube_obj)
    bpy.utils.register_class(clean_scene.MESH_OT_clean_scene)
    # register mvx test
    bpy.utils.register_class(communication.UTILS_OT_get_nonce)
    bpy.utils.register_class(communication.UTILS_OT_get_nfts)
    # register props NFTs 
    bpy.utils.register_class(communication.enum_mynfts_properties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=communication.enum_mynfts_properties)
    bpy.utils.register_class(communication.UTILS_OT_show_nft_combobox)

    preferences = LockiIdMixin.addon_prefs(bpy.context)
    preferences.reset_messages()


def unregister():
    bpy.utils.unregister_class(LockiIdLogin)
    bpy.utils.unregister_class(LockiIdLogout)
    bpy.utils.unregister_class(LockiIdPreferences)
    bpy.utils.unregister_class(LockiIdValidate)
    bpy.utils.unregister_class(AddressCheckLogin)

    # unregister scripts
    bpy.utils.unregister_class(get_scripts.MESH_OT_add_subdiv_monkey)
    bpy.utils.unregister_class(get_scripts.MESH_OT_add_rotating_cube_obj)
    
    bpy.utils.unregister_class(clean_scene.MESH_OT_clean_scene)

    # unregister mvx test
    bpy.utils.unregister_class(communication.UTILS_OT_get_nonce)
    bpy.utils.unregister_class(communication.UTILS_OT_get_nfts)

    # unregister nft list elements
    del bpy.types.Scene.my_tool
    bpy.utils.unregister_class(communication.enum_mynfts_properties)
    bpy.utils.unregister_class(communication.UTILS_OT_show_nft_combobox)

    # unregister panel 
    bpy.utils.unregister_class(VIEW3D_PT_locki_panel)

if __name__ == '__main__':
    register()
