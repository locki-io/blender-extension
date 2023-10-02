# SPDX-License-Identifier: GPL-2.0-or-later
# JNS profile stored in blender, I think we might adjust user name to herotag or bech32

import os
import bpy

from . import communication

# Set/created upon register.
profiles_path = ''
profiles_file = ''


class _BIPMeta(type):
    """Metaclass for LockiIdProfile."""

    def __str__(self):
        # noinspection PyUnresolvedReferences
        return '%s(address=%r)' % (self.__qualname__, self.address)


class LockiIdProfile(metaclass=_BIPMeta):
    """Current Locki ID profile.

    This is always stored at class level, as there is only one current
    profile anyway.
    """

    address = ''
    api_key = ''
    token = ''
    expires = ''
    nfts = {}

    @classmethod
    def reset(cls):
        cls.address = ''
        cls.api_key = ''
        cls.token = ''
        cls.expires = ''
        cls.nfts = {}

    @classmethod
    def read_json(cls):
        """Updates the active profile information from the JSON file."""

        cls.reset()

        active_profile = get_active_profile()
        if not active_profile:
            return

        for key, value in active_profile.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
            else:
                print('Skipping key %r from profile JSON' % key)

    @classmethod
    def save_json(cls, make_active_profile=False):
        """Updates the JSON file with the active profile information."""

        jsonfile = get_profiles_data()
        jsonfile['profiles'][cls.address] = {
            'api_key': cls.api_key,
            'token': cls.token,
            'expires': cls.expires,
            'nfts': cls.nfts,
        }

        if make_active_profile:
            jsonfile['active_profile'] = cls.address

        save_profiles_data(jsonfile)


def register():
    global profiles_path, profiles_file

    profiles_path = bpy.utils.user_resource(
        'CONFIG', path='locki_id', create=True)
    profiles_file = os.path.join(profiles_path, 'profiles.json')


def _create_default_file():
    """Creates the default profile file, returning its contents."""
    import json

    profiles_default_data = {
        'active_profile': None,
        'profiles': {}
    }

    os.makedirs(profiles_path, exist_ok=True)

    # Populate the file, ensuring that its permissions are restrictive enough.
    old_umask = os.umask(0o077)
    try:
        with open(profiles_file, 'w', encoding='utf8') as outfile:
            json.dump(profiles_default_data, outfile)
    finally:
        os.umask(old_umask)

    return profiles_default_data


def get_profiles_data():
    """Returns the profiles.json content from a locki_id folder in the
    locki config directory. If the file does not exist we create one with the
    basic data structure.
    """
    import json

    # if the file does not exist
    if not os.path.exists(profiles_file):
        return _create_default_file()

    # try parsing the file
    with open(profiles_file, 'r', encoding='utf8') as f:
        try:
            file_data = json.load(f)
            file_data['active_profile']
            file_data['profiles']
            return file_data
        except (ValueError,  # malformed json data
                KeyError):  # it doesn't have the expected content
            print('(%s) '
                  'Warning: profiles.json is either empty or malformed. '
                  'The file will be reset.' % __name__)

            # overwrite the file
            return _create_default_file()


def get_active_address():
    """Get the id of the currently active profile. If there is no
    active profile on the file, this function will return None.
    """

    return get_profiles_data()['active_profile']


def get_active_profile():
    """Pick the active profile from profiles.json. If there is no
    active profile on the file, this function will return None.

    @returns: dict like {'api_key': ...1234, 'username': 'email@blender.org'}
    """
    file_content = get_profiles_data()
    address = file_content['active_profile']
    if not address or address not in file_content['profiles']:
        return None

    profile = file_content['profiles'][address]
    profile['address'] = address
    return profile


def get_profile(address):
    """Loads the profile data for a given api_key if existing
    else it returns None.
    """

    file_content = get_profiles_data()
    if not address or address not in file_content['profiles']:
        return None

    profile = file_content['profiles'][address]
    return dict(
        address=profile['address'],
        api_key=profile['api_key'],
        token=profile['token']
    )


def save_profiles_data(all_profiles: dict):
    """Saves the profiles data to JSON."""
    import json

    with open(profiles_file, 'w', encoding='utf8') as outfile:
        json.dump(all_profiles, outfile, sort_keys=True)

def save_as_active_profile(auth_result: communication.AuthResult, api_key, nfts):
    """Saves the given info as the active profile."""

    LockiIdProfile.address = auth_result.address
    LockiIdProfile.token = auth_result.token
    LockiIdProfile.expires = auth_result.expires

    
    LockiIdProfile.api_key = api_key
    LockiIdProfile.nfts = nfts
  
    LockiIdProfile.save_json(make_active_profile=True)


def logout(address):
    """Invalidates the token and state of active for this user.
    This is different from switching the active profile, where the active
    profile is changed but there isn't an explicit logout.
    """
    import json

    file_content = get_profiles_data()

    # Remove user from 'active profile'
    if file_content['active_profile'] == address:
        file_content['active_profile'] = ""

    # Remove both user and token from profiles list
    if address in file_content['profiles']:
        del file_content['profiles'][address]

    with open(profiles_file, 'w', encoding='utf8') as outfile:
        json.dump(file_content, outfile)
