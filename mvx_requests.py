import bpy 
import requests.exceptions
import urllib

from . import communication

def show_message(input, message):
    def draw(self, context):
        self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title="Result for "+input, icon='INFO')

def get_nftlist_from_address(address):
    
    base_url = communication.mvx_endpoint()
    endpoint_path = 'accounts/' + address + '/nfts'
    url = urllib.parse.urljoin(base_url, endpoint_path)

    session = communication.locki_id_session()
    try:
        r = session.request('get',
                            url,
                            timeout=communication.REQUESTS_TIMEOUT)
    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        raise communication.LockiIdCommError(str(e))

    try:
        resp = r.json()
        #print(resp)
    except ValueError as e:
        raise communication.LockiIdCommError(f'Failed to decode JSON: {e}')

    if resp is None:
        raise communication.LockiIdCommError('NFT not found in response')

    return resp

def get_urllist_from_list(nftlist):
    result = []
    for item in nftlist:
        if 'assets' in item and item['assets']:
            identifier = item['identifier']
            assets = item['assets']
            svg_url = assets.get('svgUrl','')
            png_url = assets.get('pngUrl','')

            result.append({
                'identifier': identifier,
                'svgUrl': svg_url,
                'pngUrl': png_url,
            })

        if 'media' in item and item['media']:  # Check if 'media' key exists and is not empty
            identifier = item['identifier']
            media = item['media'][0]  # Assuming 'media' is a list and taking the first element
            uris = item.get('uris', [])  # Get 'uris' or default to an empty list if it doesn't exist
            
            # Extracting required fields from 'media'
            original_url = media.get('originalUrl', '')
            thumbnail_url = media.get('thumbnailUrl', '')
            url = media.get('url', '')

            # Formatting uris
            uri_dict = {f'uri{i + 1}': uri for i, uri in enumerate(uris)}
        
            result.append({
                'identifier': identifier,
                'originalUrl': original_url,
                'thumbnailUrl': thumbnail_url,
                'url': url,
                **uri_dict  # This syntax merges the uri_dict into the result dictionary
            })
    return result

def check_address_nonce(address):
    import requests.exceptions
    import urllib
    
    base_url = communication.mvx_endpoint()
    endpoint_path = 'address/' + address + '/nonce'
    url = urllib.parse.urljoin(base_url, endpoint_path)

    session = communication.locki_id_session()
    try:
        r = session.request('get',
                            url,
                            timeout=communication.REQUESTS_TIMEOUT)
    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        raise communication.LockiIdCommError(str(e))

    try:
        resp = r.json()
        print(resp)
    except ValueError as e:
        raise communication.LockiIdCommError(f'Failed to decode nonce JSON: {e}')

    if resp is None:
        raise communication.LockiIdCommError('Nonce not found in response (address empty)')
    else:
         # Assume the desired value is in a key called 'desired_key' in the JSON structure
        nonce = resp.get('data', {}).get('nonce', None)
        result = {"nonce": nonce,"address": address}
            
    return result
