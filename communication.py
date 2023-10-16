# SPDX-License-Identifier: GPL-2.0-or-later

import functools
import logging
import typing

log = logging.getLogger(__name__)

# Can be overridden by setting the environment variable LOCKI_ID_ENDPOINT. Overrid with localhost:3000 for development
LOCKI_ID_ENDPOINT = 'http://api.locki.io'  
MVX_ENDPOINT = 'https://devnet-api.multiversx.com/'
AUTH_ENDPOINT = 'https://2rkm8gkhk7.execute-api.eu-central-1.amazonaws.com/'


# Will become a requests.Session at the first request to Locki ID.
requests_session = None
load_session = None

# Request timeout, in seconds.
REQUESTS_TIMEOUT = 10.0

class LockiIdCommError(RuntimeError):
    """Raised when there was an error communicating with Locki ID"""

class AuthResult:
    def __init__(self, *, success: bool, address: str = None,
                 token: str = None, expires: int = 1697228561601,
                 error_message: typing.Any = None):  # when success=False
        self.success = success
        self.address = address
        #self.api_key = api_key
        self.token = token
        self.error_message = str(error_message)
        self.expires = expires

@functools.lru_cache(maxsize=None)
def host_label():
    import socket

    # info on where Blender is running
    return 'Blender running on %r' % socket.gethostname()

def load_nft_session():
# Returns the loading session, creating it if necessary.
# The load session is necessary because authorizing on some website returns error
    global load_session
    import requests.adapters

    if load_session is not None:
        return load_session

    load_session = requests.session()

    retries = requests.packages.urllib3.util.retry.Retry(
        total=5,
        backoff_factor=0.05,
    )
    http_adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    load_session.mount('https://', http_adapter)
    load_session.mount('http://', http_adapter)

    # Construct the User-Agent header with Blender and add-on versions.
    try:
        import bpy
    except ImportError:
        blender_version = 'unknown'
    else:
        blender_version = '.'.join(str(component)
                                   for component in bpy.app.version)

    from blender_id import bl_info
    from . import bl_info as bl_info_addon 
    # addon_version = '.'.join(str(component) for component in bl_info['version'])
    addon_version = bl_info_addon['version']
    load_session.headers['User-Agent'] = f'Blender/{blender_version} Locki-ID-Addon/{ addon_version }'

    return load_session

def locki_id_session(token: str = None):
    """Returns the Requests session, creating it if necessary."""
    global requests_session
    import requests.adapters

    if requests_session is not None:
        return requests_session

    requests_session = requests.session()

    #DEBUGGING
    # no Host in header ???? print(requests_session.headers['Host'])

    # Retry with backoff factor, so that a restart of Blender ID or hickup
    # in the connection doesn't immediately fail the request.
    retries = requests.packages.urllib3.util.retry.Retry(
        total=5,
        backoff_factor=0.05,
    )
    http_adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    requests_session.mount('https://', http_adapter)
    requests_session.mount('http://', http_adapter)

    # Construct the User-Agent header with Blender and add-on versions.
    try:
        import bpy
    except ImportError:
        blender_version = 'unknown'
    else:
        blender_version = '.'.join(str(component)
                                   for component in bpy.app.version)

    from blender_id import bl_info
    from . import bl_info as bl_info_addon 
    # addon_version = '.'.join(str(component) for component in bl_info['version'])
    addon_version = bl_info_addon['version']
    requests_session.headers['User-Agent'] = f'Blender/{blender_version} Locki-ID-Addon/{ addon_version }'
    if token is not None:
        requests_session.headers['Authorization'] = token
    return requests_session

@functools.lru_cache(maxsize=None)
def auth_endpoint(endpoint_path=None):
    """Gets the endpoint for the authentication API. If the MVX_ENDPOINT env variable
    is defined, it's possible to override the (default) production address.
    """
    import os
    import urllib.parse

    base_url = os.environ.get('AUTH_ENDPOINT')
    if base_url:
        log.warning('Using overridden SL url %s', base_url)
    else:
        base_url = AUTH_ENDPOINT
        log.info('Using standard SL url %s', base_url)

    # urljoin() is None-safe for the 2nd parameter.
    return urllib.parse.urljoin(base_url, endpoint_path)

@functools.lru_cache(maxsize=None)
def mvx_endpoint(endpoint_path=None):
    """Gets the endpoint for the authentication API. If the MVX_ENDPOINT env variable
    is defined, it's possible to override the (default) production address.
    """
    import os
    import urllib.parse

    base_url = os.environ.get('MVX_ENDPOINT')
    if base_url:
        log.warning('Using overridden mvx url %s', base_url)
    else:
        base_url = MVX_ENDPOINT
        log.info('Using standard mvx url %s', base_url)

    # urljoin() is None-safe for the 2nd parameter.
    return urllib.parse.urljoin(base_url, endpoint_path)

def mvx_authenticate(address, token) -> AuthResult:
    import requests.exceptions

    # Payload is optional (GET) 
    payload = dict(
        address=address,
        host_label=host_label()
    )

    url = mvx_endpoint(u'/address/' + address + u'/nonce')
    session = locki_id_session(token)
    try:
        r = session.get(url, data=payload, verify=True,
                         timeout=REQUESTS_TIMEOUT)
    except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        msg = 'Exception GETing to {}: {}'.format(url, e)
        print(msg)
        return AuthResult(success=False, error_message=msg)

    if r.status_code == 200:
        resp = r.json()
        status = resp['code']
        if status == 'successful':
            # defines the structure of the payload server side response
            return AuthResult(success=True
                              )
        if status == 'fail':
            return AuthResult(success=False, error_message='address is incorrect')

    return AuthResult(success=False,
                      error_message='There was a problem communicating with'
                                    ' the server. Error code is: %s' % r.status_code)


@functools.lru_cache(maxsize=None)
def locki_id_endpoint(endpoint_path=None):
    """Gets the endpoint for the authentication API. If the LOCKI_ID_ENDPOINT env variable
    is defined, it's possible to override the (default) production address.
    """
    import os
    import urllib.parse

    base_url = os.environ.get('LOCKI_ID_ENDPOINT')
    if base_url:
        log.warning('Using overridden Locki ID url %s', base_url)
    else:
        base_url = LOCKI_ID_ENDPOINT
        log.info('Using standard Locki ID url %s', base_url)

    # urljoin() is None-safe for the 2nd parameter.
    return urllib.parse.urljoin(base_url, endpoint_path)

def locki_id_server_authenticate( token ) -> AuthResult:
    """Authenticate the user with the server with a single transaction
    containing api_key (must happen via HTTPS).

    If the transaction is successful, status will be 'successful' and we
    return the user's token (that will be used to authenticate).
    If there was a problem, status will be 'fail' and we return an error
    message. Problems may be with the connection or wrong api_key.
    """

    import requests.exceptions

    payload = dict(
        #token=token,
        #host_label=host_label()
    )
    # the locki api server need an identify endpoint
    # create the route the API /identity
    url = auth_endpoint(u'/Prod/identity')
    session = locki_id_session(token)
    user_agent = session.headers.get('User-Agent')
    host = session.headers.get('Host')
    print ('User-agent :' + user_agent)
    try:
        r = session.get(url, verify=True,
                         timeout=REQUESTS_TIMEOUT)
    except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        msg = 'Exception GETing to {}: {}'.format(url, e)
        print(msg)
        return AuthResult(success=False, error_message=msg)

    if r.status_code == 200:
        resp = r.json()
        return AuthResult(success=True, address=resp['address'], expires=resp['expires']*1000)
        # status = resp['status_code']
        #nativeAuthToken = resp['nativeAuthToken']
        #if nativeAuthToken is not None: # status == 'success':
            # defines the structure of the payload server side response
        #    return AuthResult(success=True,
        #                      token=resp['nativeAuthToken'],
        #                      expires=resp['expiry'], 
        #                      )
        #else: #if status == 'fail':
        #    return AuthResult(success=False, error_message='api-key is incorrect')

    return AuthResult(success=False,
                      error_message='There was a problem communicating with'
                                    ' the server. Error code is: %s' % r.status_code)


def locki_id_server_validate(token) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
    """Validate the nativeAuth token with the server.
        JNS question is whether we validate with the chain ? or with the locki server

    @param token: the authentication token
    @type token: str
    @returns: tuple (expiry, error).
        The expiry is the expiry date of the token if it is valid, else None.
        The error is None if the token is valid, or an error message when it's invalid.
    """

    import requests.exceptions

    url = mvx_endpoint(u'/validate_token')  # JNS change route to transaction to pingpong
    session = locki_id_session(token)
    try:
        r = session.post(url, data={'token': token},
                         verify=True, timeout=REQUESTS_TIMEOUT)
    except requests.exceptions.ConnectionError:
        log.exception('error connecting to Locki ID at %s', url)
        return None, 'Unable to connect to Locki ID'
    except requests.exceptions.RequestException as e:
        log.exception('error validating token at %s', url)
        return None, str(e)

    if r.status_code != 200:
        return None, 'Authentication token invalid'

    response = r.json()
    return response['token_expires'], None


def locki_id_server_logout(address, token):
    """Logs out of the Locki ID service by removing the token server-side.

    @param api_key: the apikey of the user.
    @type api_key: str
    @param token: the token to remove
    @type token: str
    @return: {'status': 'fail' or 'success', 'error_message': str}
    @rtype: dict
    """

    import requests.exceptions

    payload = dict(
        address=address,
        token=token
    )
    session = locki_id_session(token)
    try:
        r = session.post(locki_id_endpoint(u'/delete_token'),
                         data=payload, verify=True, timeout=REQUESTS_TIMEOUT)
    except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        return dict(
            status='fail',
            error_message=format('There was a problem setting up a connection to '
                                 'the server. Error type is: %s' % type(e).__name__)
        )

    if r.status_code != 200:
        return dict(
            status='fail',
            error_message=format('There was a problem communicating with'
                                 ' the server. Error code is: %s' % r.status_code)
        )

    resp = r.json()
    return dict(
        status=resp['status'],
        error_message=None
    )

def make_authenticated_call(method, url, token, data):
    """Makes a HTTP call authenticated with the nativeAuth token."""

    import requests.exceptions

    session = locki_id_session(token)
    try:
        r = session.request(method,
                            mvx_endpoint(url),
                            data=data,
                            headers={
                                'Authorization': 'Bearer %s' % token},
                            verify=True,
                            timeout=REQUESTS_TIMEOUT)
    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        raise LockiIdCommError(str(e))

    return r