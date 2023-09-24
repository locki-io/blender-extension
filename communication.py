# SPDX-License-Identifier: GPL-2.0-or-later

import functools
import logging
import typing

log = logging.getLogger(__name__)

# Can be overridden by setting the environment variable LOCKI_ID_ENDPOINT. Overrid with localhost:8000 for development
LOCKI_ID_ENDPOINT = 'https://api.locki.io/'

# Will become a requests.Session at the first request to Locki ID.
requests_session = None

# Request timeout, in seconds.
REQUESTS_TIMEOUT = 5.0


class LockiIdCommError(RuntimeError):
    """Raised when there was an error communicating with Locki ID"""


class AuthResult:
    def __init__(self, *, success: bool,
                 user_id: str = None, token: str = None, expires: str = None,
                 error_message: typing.Any = None):  # when success=False
        self.success = success
        self.user_id = user_id
        self.token = token
        self.error_message = str(error_message)
        self.expires = expires


@functools.lru_cache(maxsize=None)
def host_label():
    import socket

    # info on where Blender is running
    return 'Blender running on %r' % socket.gethostname()


def locki_id_session():
    """Returns the Requests session, creating it if necessary."""
    global requests_session
    import requests.adapters

    if requests_session is not None:
        return requests_session

    requests_session = requests.session()

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
    addon_version = '.'.join(str(component)
                             for component in bl_info['version'])
    requests_session.headers['User-Agent'] = f'Blender/{blender_version} Locki-ID-Addon/{addon_version}'

    return requests_session


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


def locki_id_server_authenticate(key, secret) -> AuthResult:
    """Authenticate the user with the server with a single transaction
    containing key and secret (must happen via HTTPS).

    If the transaction is successful, status will be 'successful' and we
    return the user's unique locki id uuid and a token (that will be used to
    represent that key and secret combination).
    If there was a problem, status will be 'fail' and we return an error
    message. Problems may be with the connection or wrong key/secret.
    """

    import requests.exceptions

    payload = dict(
        key=key,
        secret=secret,
        host_label=host_label()
    )
    # the locki api server need an identify param

    # JNS create the route the API /identity
    url = locki_id_endpoint('u/identify')
    session = locki_id_session()
    try:
        r = session.post(url, data=payload, verify=True,
                         timeout=REQUESTS_TIMEOUT)
    except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        msg = 'Exception POSTing to {}: {}'.format(url, e)
        print(msg)
        return AuthResult(success=False, error_message=msg)

    if r.status_code == 200:
        resp = r.json()
        status = resp['status']
        if status == 'success':
            # defines the structure of the payload server side response
            return AuthResult(success=True,
                              user_id=str(resp['data']['user_id']),
                              # JNS to update as bearer token nativeAuth
                              token=resp['data']['oauth_token']['access_token'],
                              expires=resp['data']['oauth_token']['expires'],
                              )
        if status == 'fail':
            return AuthResult(success=False, error_message='Username and/or password is incorrect')

    return AuthResult(success=False,
                      error_message='There was a problem communicating with'
                                    ' the server. Error code is: %s' % r.status_code)


def locki_id_server_validate(token) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
    """Validate the auth token with the server.

    @param token: the authentication token
    @type token: str
    @returns: tuple (expiry, error).
        The expiry is the expiry date of the token if it is valid, else None.
        The error is None if the token is valid, or an error message when it's invalid.
    """

    import requests.exceptions

    url = locki_id_endpoint('u/validate_token')  # JNS route to make up
    session = locki_id_session()
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


def locki_id_server_logout(user_id, token):
    """Logs out of the Locki ID service by removing the token server-side.

    @param user_id: the email address of the user.
    @type user_id: str
    @param token: the token to remove
    @type token: str
    @return: {'status': 'fail' or 'success', 'error_message': str}
    @rtype: dict
    """

    import requests.exceptions

    payload = dict(
        user_id=user_id,
        token=token
    )
    session = locki_id_session()
    try:
        r = session.post(locki_id_endpoint('u/delete_token'),
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


def make_authenticated_call(method, url, auth_token, data):
    """Makes a HTTP call authenticated with the OAuth token."""

    import requests.exceptions

    session = locki_id_session()
    try:
        r = session.request(method,
                            locki_id_endpoint(url),
                            data=data,
                            headers={
                                'Authorization': 'Bearer %s' % auth_token},
                            verify=True,
                            timeout=REQUESTS_TIMEOUT)
    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        raise LockiIdCommError(str(e))

    return r
