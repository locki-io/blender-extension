# SPDX-License-Identifier: GPL-2.0-or-later

import logging  # from blender cloud addon
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import PointerProperty, BoolProperty, StringProperty, IntProperty, CollectionProperty, EnumProperty
from bpy.types import AddonPreferences, Context, Operator, PropertyGroup, Menu
import bpy
import typing
import datetime

bl_info = {
    'name': 'Locki_id_Addon',
    'author': 'Satish NVRN, George Călin Pîrîială, Jean-Noël Schilling',
    'version': (0, 1, 7),
    'blender': (3, 6, 2),
    'location': 'Add-on preferences + navigate to 3D view panel',
    'tracker_url': 'https://github.com/locki-io/locki_id_addon/',
    'doc_url' : 'https://app.locki.io/profile/',
    'description':
        'Stores your Locki ID credentials(NativeAuthToken) for usage of your stored NFTs',
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
else:
    from . import communication, profiles, mvx_requests
    from .scripts import clean_scene
    from .scripts import get_scripts

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
    openAi: StringProperty(
        name='API KEY',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='PASSWORD'
    )
    token: StringProperty(
        name='NativeAuthToken',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    nonce: IntProperty(
        name='nonce', 
        default= 0
    )
    nfts_enum: EnumProperty(
        items=[('default', "default", "Choose your nft")],
        # Enumeration of the nfts it is an object
        name='All my NFTs',  # Default item
        default='default',
        description='Formated enumeration of the NFTs',
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
                        'You are logged with NativeAuthToken %s') % active_profile.token
                else:
                    msg = tip_('You are logged in as %s at %s') % (
                        active_profile.token, endpoint)

                col = layout.column(align=True)
                col.label(text=msg, icon='WORLD_DATA')
                if time_left.days < 14:
                    col.label(text=tip_('Your token will expire %s. Please log out and log in again '
                                        'to refresh it') % exp_str, icon='PREVIEW_RANGE')
                else:
                    col.label(text=tip_('Your authentication token expires %s') % exp_str,
                              icon='BLANK1')

            row = layout.row().split(factor=1)
            row.operator('locki_id.logout')
            # row.operator('locki_id.validate')
            
        else:
            col = layout.column(align=True)
            msg = tip_('You are not logged in yet')
            col.label(text=msg, icon='INFO')
            col.label(text=tip_('get your NativeAuth token on app.locki.io/profile (hit Documentation button)'), icon='PREVIEW_RANGE')
            layout.prop(self, 'address')
            layout.prop(self, 'token')

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

        requests_session = None
        auth_result = communication.locki_id_server_authenticate(
            #address=addon_prefs.address,
            token=addon_prefs.token,
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
                addon_prefs.token,
                {},
                "0",
            )
            addon_prefs.ok_message = tip_('Logged in')
        else:
            addon_prefs.error_message = auth_result.error_message
            if LockiIdProfile.address:
                profiles.logout(LockiIdProfile.address)

        # After logging in, call the update_nfts_data function to populate nfts_data
        update_nfts_data(self, context)

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
        requests_session = None
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
        locki = context.scene.locki
        nft_list = mvx_requests.get_nftlist_from_address(LockiIdProfile.address)
        nft_urls = mvx_requests.get_urllist_from_list(nft_list)

        # store them into the profile 
        LockiIdProfile.nfts = nft_urls

        records = mvx_requests.transform_nft_urls_in_menu(nft_urls)
        print(records)

        # Update the nfts_enum property in addon preferences
        # addon_prefs.nfts_enum = formatted_records
        # debugging the result : 
        # print(test)
        count = len(records)-1
        mvx_requests.show_message(LockiIdProfile.address, f"{count} NFTs loaded")
        #content_menu_nft = mvx_requests.transform_nft_urls_in_menu(nft_urls)
        #print(content_menu_nft)
        #LockiIdPreferences.nfts_collection = content_menu_nft
        # nfts_collection is readonly but I would like to do that:
        #addon_prefs.nfts_collection = mvx_requests.transform_nft_urls_in_menu(nft_urls)
        #expect a string enum not a list
        LockiIdProfile.save_json()

        addon_prefs.ok_message = tip_('You have loaded the NFTs')
        LockiIdProfile.read_json()

        return {"FINISHED"}

import bpy
import tempfile
import os
import urllib.request
import ssl

def load_url_as_object(url, file_format, location=(0,0,0)):
    import os
    import tempfile
    # Disable SSL certificate verification (not recommended)
    ssl._create_default_https_context = ssl._create_unverified_context
    """Option 2: Configure Blender to Use a Trusted Certificate Bundle (Recommended)
    It's a better practice to configure Blender to use a trusted certificate bundle. You can download a certificate bundle file (e.g., cacert.pem) from a trusted source (e.g., Mozilla) and specify it in your Blender user preferences.
    Here's how to do it:
    Download the certificate bundle file (cacert.pem) from a trusted source. One such source is the Mozilla CA Certificate Program: https://curl.se/docs/caextract.html
    In Blender, go to Edit > Preferences.
    In the Preferences window, navigate to the "System" tab.
    Under the "SSL Certificate Bundle" section, click the "Open" button to browse and select the downloaded certificate bundle file (cacert.pem).
    Save your preferences.
    After configuring Blender to use a trusted certificate bundle, it should be able to perform SSL certificate verification correctly when making HTTPS requests.
    """
    supported_formats = {'SVG', 'GLB', 'PY'}  # Add more formats if needed

    if file_format not in supported_formats:
        print(f"Unsupported file format: {file_format}")
        return
    
    if file_format == 'GLB':
        session = communication.load_nft_session()
        r = session.get(url, verify=True)
        if r.status_code == 200:
            print(f"passed with 200")
            # Use Blender's temporary directory
            temp_dir = bpy.path.abspath("//temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Construct the local file path for the downloaded file
            file_name = os.path.basename(url)
            local_path = os.path.join(temp_dir, file_name)

            # Write the content of the response to the local file
            with open(local_path, 'wb') as f:
                f.write(r.content)

            # Import the downloaded GLB file as an object in Blender
            bpy.ops.import_scene.gltf(filepath=local_path, filter_glob="*.glb")
        else: 
            print(f"Error in downloading the obj/mesh file: {r.status_code} - {r.text}")

    if file_format == 'PY':
        session = communication.load_nft_session()
        r = session.get(url, verify=True)
        if r.status_code == 200:
            print(f"passed with 200")
            # Use Blender's temporary directory
            temp_dir = bpy.path.abspath("//temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Construct the local file path for the downloaded file
            file_name = os.path.basename(url)
            local_path = os.path.join(temp_dir, file_name)

            # Write the content of the response to the local file
            with open(local_path, 'wb') as f:
                f.write(r.content)

            try:
                # Find the newly created Text Editor area
                text_editor_area = None
                # Iterate through all text data-blocks and unlink them
                for text in bpy.data.texts:
                    bpy.data.texts.remove(text)

                # Create a new text block
                new_text_block = bpy.data.texts.new(name=file_name)

                # Load the content of the Python file into the text block
                with open(local_path, 'r') as f:
                    new_text_block.from_string(f.read())

                for area in bpy.context.screen.areas:
                    if area.type == 'TEXT_EDITOR':

                        text = bpy.data.texts[file_name]
                        text.use_fake_user = True  # Ensure the script is saved
                        
                        # Method 1 Switch to the Text Editor mode
                        area.spaces[0].text = text # make loaded text file visible
                        ctx = bpy.context.copy()
                        ctx['edit_text'] = text
                        ctx['area'] = area
                        ctx['region'] = area.regions[-1] # ... just modify the view area
                        # Crashes Blender
                        # bpy.ops.text.run_script(ctx) #running the script

                        bufferName = file_name
                        lib = bpy.data.texts[bufferName].as_string()
                        exec(lib)
                        bpy.ops.screen.animation_play()
                        break 

            except Exception as e:
                print(f"Error loading Python file in the text editor area: {e}")
            finally:
                clean_up_tempfile(temp_dir)

        else: 
            print(f"Error in downloading the python file: {r.status_code} - {r.text}")

    elif file_format == 'SVG':
        # Create a temporary directory to store the downloaded file
        temp_dir = tempfile.mkdtemp()
        try:
            # Construct the local file path for the downloaded file
            file_name = os.path.basename(url)
            local_path = os.path.join(temp_dir, file_name)

            # Download the file from the URL
            urllib.request.urlretrieve(url, local_path)

            # Import the downloaded file as an object in Blender
            if file_format == 'OBJ':
                bpy.ops.import_scene.obj(filepath=local_path)
            elif file_format == 'FBX':
                bpy.ops.import_scene.fbx(filepath=local_path)
            elif file_format == 'STL':
                bpy.ops.import_mesh.stl(filepath=local_path)
            elif file_format == 'SVG':
                bpy.ops.import_curve.svg(filepath=local_path , filter_glob="*.svg")
            # Add more import formats as needed

        except Exception as e:
            print(f"Error loading URL as object: {e}")
        finally:
            clean_up_tempfile(temp_dir)

def clean_up_tempfile(temp_dir):
# Clean up: remove the temporary directory and its contents
    if os.path.exists(temp_dir):
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(temp_dir)

class UTILS_OT_load_nft(LockiIdMixin, bpy.types.Operator):


    bl_idname= "utils.load_nft"
    bl_label= "Load your NFT here"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        import webbrowser
        locki = context.scene.locki

        # capital file_format for loading 
        file_type = url_to_file_type(locki.nfts_collection)
        if locki.nfts_collection and "dataNftView" in locki.nfts_collection and file_type == '':
            # Open a URL in the default web browser
            webbrowser.open(locki.nfts_collection)
            return {"FINISHED"}
        # locki.nfts_collection load the file 
        else:
            load_url_as_object(locki.nfts_collection, file_type)

        return {"FINISHED"}


def url_to_file_type(url):
    import os
    from urllib.parse import urlparse
    # Parse the URL to extract the path component
    parsed_url = urlparse(url)
    # Get the path from the parsed URL
    path = parsed_url.path
    # Use os.path.splitext to extract the file extension
    _, file_extension = os.path.splitext(path)
    # Remove the dot and convert to uppercase
    file_extension = file_extension.lstrip('.').upper()

    return file_extension

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

    def prepare(self, context):        
        sce = context.scene
        self.recall_mode = context.object.mode
        update_nfts_data(self, context)

    def invoke(self, context, event):
        update_nfts_data(self, context)

    def draw(self, context):
        """Load the addons_prefs"""
        addon_prefs = self.addon_prefs(context)
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
            # preferences = context.preferences.addons[__name__].preferences            
            # nfts_collection = addon_prefs.nfts

            # Add items based on your nfts_collection
            # for items in nfts_collection:
            #     items.append((items.identifier, items.description, items.url))  # Use the data from your collection
            
            # Display the combobox
            box = layout.box()
            row = box.row(align=True)
            row.label(text='My NFTs')
            row.prop(locki, "ui_expanded_nft", text=('HIDE' if locki.ui_expanded_nft else 'SHOW'), 
                              icon=('TRIA_DOWN' if locki.ui_expanded_nft else 'TRIA_RIGHT'))
            if locki.ui_expanded_nft:
                box.prop(locki,"nfts_collection", text="my NFTs",icon='COLLECTION_NEW', emboss=True)
                row = box.row(align=True)
                row.prop(locki, "file_format")
                #row = box.row(align=True)
                #row.prop(locki, "my_selected_nft", text="url")
                row = box.row(align=True)
                row.operator("utils.load_nft", text="LOAD")
 
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

    # store the NFTs in addon_prefs 
    # Define a PropertyGroup to represent items in the combobox

def update_nfts_data(self, context):
    items = []  # Clear the collection first
    stream_only = False
    data_nft = context.scene.locki.nfts_data
    # Access LockiIdProfile.nfts and populate nfts_data
    for identifier, data in LockiIdProfile.nfts.items():
        compatible_extensions = ['.svg', '.glb', '.gltf', '.py', '.step']
        filter_on = context.scene.locki.file_format
        if filter_on == 'none':
            extensions = compatible_extensions
        elif filter_on == '.gltf':
            specific_extensions = ['.gltf', '.glb']
            extensions = [ext for ext in compatible_extensions if ext in specific_extensions]
        elif filter_on == 'streamonly':
            stream_only = True
        else:
            specific_extensions = [filter_on]
            extensions = [ext for ext in compatible_extensions if ext in specific_extensions]
        #print(extensions)
        for key, url in data.items():
            # special treatment of lockiUrl to get to the datastream
            #print(filter_on)
            if (key == 'lockiUrl') and (filter_on == 'none' or filter_on == 'streamonly'):
                items.append((url , f'{identifier}-{key}', f"{url.split('/')[-1]} of {identifier}"))
            if stream_only == False:
                if url is not None and (key.endswith("Url") or key.startswith("uri")) and any(url.endswith(ext) for ext in extensions):
                    items.append((url , f'{identifier}-{key}', f"Link to Datasteam of {identifier}"))

    if items is None:
        items = [("default", "default", "Choose your nft")]
    
    return items

# Callback function to update my_selected_nft
def update_selected_nft_url(self, context):
    selected_item = context.scene.locki.nfts_data[context.scene.locki.nfts_collection]
    if selected_item:
        context.scene.locki.my_selected_nft = selected_item.url
    else:
        context.scene.locki.my_selected_nft = ""

class NftDataItem(PropertyGroup):
    identifier: StringProperty()
    name: StringProperty()
    url: StringProperty()

class SceneProperties(PropertyGroup):
    file_format: EnumProperty(
        name="Filter",
        description="The file format of your NFT",
        items=(
            ('none', "no Filter", ""),
            ('streamonly',"View DataStream","View my private data"),
            ('.svg', "SVG", "Filter only SVG content"),
            ('.py', "PY", "Filter only python code content"),
            ('.gltf', "GLTF or GLB", "Filter only gltf objects"),
        ),
        default='none',
    )
    ui_expanded_nft: BoolProperty(
        name="Show Nfts Expanded",
        description="Shows the box 'Nfts choice' expanded in user interface",
        default=True, 
        options={'SKIP_SAVE'}
        )
    
    # Define your custom property for the Scene object
    my_selected_nft: StringProperty(
        name="My Selected Nft",
        default="",
        description="A description for my selected NFT"
    )
    nfts_data: bpy.props.CollectionProperty(
        type=NftDataItem,
        name="My Nfts Data",
        description='All loaded Nfts by identifier',
    )

    # Define a CollectionProperty to store items for the combobox
    nfts_collection: EnumProperty(
        items=update_nfts_data,
        name="My Nfts",
        # default=1,        
        description='All loaded Nfts by identifier',
        #update=update_selected_nft_url
    )
 
def get_selected_text():
    import re
    # Check if we are in the Text Editor
    if bpy.context.area.type == 'TEXT_EDITOR':
        # Get the active text data-block
        text = bpy.context.space_data.text

        # Check if any text is selected
        if text:
            text_selection = bpy.context.edit_text
            active_text = bpy.context.area.spaces.active.text
            # Set the selection range
            cli = text_selection.current_line_index
            eli = text_selection.select_end_line_index
            store_text = ''
            # Define a regular expression pattern to match tabs
            tab_pattern = re.compile(r'    ')

            if  cli <= eli:
                while cli <= eli:
                    store_text += tab_pattern.sub(r'\t',text_selection.current_line.body)
                    store_text += '\n'
                    cli += 1
                    text_selection.select_set(line_start=cli, char_start=0,  line_end=cli+1, char_end=0)
            else:
                text_selection.select_set(line_start=eli, char_start=0,  line_end=eli, char_end=0)
                temp = cli
                cli = eli
                eli = temp
                while cli <= eli:
                    store_text += tab_pattern.sub(r'\t',text_selection.current_line.body)
                    store_text += '\n'
                    cli += 1
                    text_selection.select_set(line_start=cli, char_start=0,  line_end=cli+1, char_end=0)
                      
            # Replace tabs with spaces to preserve indentation
            store_text = store_text.replace('\t', '\\t')
            store_text = store_text.replace('\n', '\\n')
            text_selection.select_set(line_start=cli, char_start=0,  line_end=eli+1, char_end=0)
           
            return store_text
    # If not in the Text Editor or no text is selected, return None
    return None

class AiOperator(Operator):
    bl_idname = "text.ai_operator"
    bl_label = "Artificial intelligence Operator"

    def execute(self, context):
        # Your custom operator logic goes here
        import webbrowser
        locki = context.scene.locki
        helpMeString = get_selected_text()
        ai_help_url = 'https://chat.locki.io?string=' + helpMeString 
        webbrowser.open(ai_help_url)

        return {'FINISHED'}

def ai_menu_func(self, context):
    self.layout.operator("text.ai_operator", text="Update this script with locki AI")

module_classes = (
    NftDataItem,
    SceneProperties,

    LockiIdLogin,
    LockiIdLogout,
    LockiIdPreferences,
    LockiIdValidate,

    UTILS_OT_get_nfts, # register utility operators
    UTILS_OT_get_nonce, # Register utility operators
    UTILS_OT_load_nft, # Let us load !

    get_scripts.MESH_OT_add_subdiv_monkey, # Register mesh and scene utilities
    get_scripts.MESH_OT_add_rotating_cube_obj, # Register mesh and scene utilities
    clean_scene.MESH_OT_clean_scene, # Register mesh and scene utilities

    VIEW3D_PT_locki_panel, # register panel
    #AiLockiTextEditorMenu,
    AiOperator

)


def register():
    # Register profile and data-related functionalities
    profiles.register()

    for cls in module_classes:
        bpy.utils.register_class(cls)

    # Define a full scene (UI) reserved for the addon all defined in Class Scene property
    bpy.types.Scene.locki = PointerProperty(type=SceneProperties)
    bpy.types.TEXT_MT_context_menu.append(ai_menu_func)

    LockiIdProfile.read_json()
    # Reset messages or any final initialization
    preferences = LockiIdMixin.addon_prefs(bpy.context)
    preferences.reset_messages()


def unregister():
    # Unregister the update handler for nfts_collection
    # del bpy.types.Scene.locki.nfts_collection
    # Reset messages or any final de-initialization
    preferences = LockiIdMixin.addon_prefs(bpy.context)
    preferences.reset_messages()  # Assuming you might want to clean up some stuff during unregister as well.
    bpy.types.TEXT_MT_context_menu.remove(ai_menu_func)

    # Unregister Classes in reverse order
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()
