import bpy 
import requests.exceptions
import urllib
import base64
import binascii


from . import communication
from . import profiles

def show_message(input, message):
    def draw(self, context):
        self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title="Result for "+input, icon='INFO')

def clear_url_64(url):
    # First, decode the base64 string to get a hex string
    output_str = base64.b64decode(url).decode('utf-8')
    return output_str

def decode_base64(data):
    """Decodes base64, padding being optional."""
    missing_padding = len(data) % 4
    if missing_padding:
        data += '='* (4 - missing_padding)
    return base64.b64decode(data).decode('utf-8')

def transform_nft_urls_in_menu(nft_url):
    nft_identifiers = [("default", "default", "Choose your nft")]
    #print(nft_url)
    for identifier, data in nft_url.items():
        #print(data)
        for key, url in data.items():
            #compatible file extension 
            compatible_extensions = ['.svg', '.glb', '.glbt', '.py', 'step']
            if url is not None and (key.endswith("Url") or key.startswith("uri")) and any(url.endswith(ext) for ext in compatible_extensions):
                # Append to the tuple in the format you mentioned
                nft_identifiers.append((f'{identifier}-{key}', f"{url.split('/')[-1]} of {identifier}", url))

    return nft_identifiers


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

def extract_data_preview_url(metadata_json_url):
    import json
    import requests

    try:
        response = requests.get(metadata_json_url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Get the content of the response
            content = response.text
            # Load the metadata JSON loaded from the file)
            metadata = json.loads(content)
        else:
            print(f"Failed to retrieve content. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    # Initialize the URL to None in case "Data Preview URL" is not found
    dataPreviewUrl = None

    # Search for the "Data Preview URL" trait in the attributes list
    for attribute in metadata.get("attributes", []):
        if attribute.get("trait_type") == "Data Preview URL":
            dataPreviewUrl = attribute.get("value")
            break  # Exit the loop once found

    return dataPreviewUrl

def get_urllist_from_list(nftlist):
    result = {}
    for item in nftlist:
        # TODO Here load the datatypes from MvX and handle smart
        # Standard NFT with assets (defi SFT)
        if 'assets' in item and item['assets']:
            identifier = item['identifier']
            name = item['name'] 
            attributes = item.get('attributes','')
            assets = item['assets']
            svg_url = assets.get('svgUrl','')
            png_url = assets.get('pngUrl','')

            result[identifier] = {
                'attributes' : attributes,
                'name' : name,
                'svgUrl': svg_url,
                'pngUrl': png_url,
            }
            continue
        # DATANFT from collection
        if (item['collection'] == 'DATANFTFT4-3ba099'):  # Check if 'media' key exists and is not empty
            identifier = item['identifier']
            name = item['name']
            nonce = item['nonce']
            attributes = item.get('attributes','')
            media = item['media'][0]  # Assuming 'media' is a list and taking the first element
            uris = item.get('uris', [])  # Get 'uris' or default to an empty list if it doesn't exist
            
            # Extracting required fields from 'media'
            original_url = media.get('originalUrl', '')
            thumbnail_url = media.get('thumbnailUrl', '')
            url = media.get('url', '')

            # Decoding and formatting uris
            decoded_uris = [clear_url_64(uri) for uri in uris]
            uri_dict = {f'uri{i + 1}': decoded_uri for i, decoded_uri in enumerate(decoded_uris)}
            
            # Create a url for the Datastream in app.locki.io 

            lockiUrl = 'https://app.locki.io/datanftview?nonce=' + str(nonce) + '&nativeauthtoken=' + profiles.LockiIdProfile.token
            # Check if the end of the decoded URIs is "metadata.json"
            if decoded_uris and decoded_uris[-1].endswith("metadata.json"):
            # If "metadata.json" is found at the end, set data_preview_url
                dataPreviewUrl = extract_data_preview_url(decoded_uris[-1])
            else:
                dataPreviewUrl = None

            result[identifier]= {
                'attributes' : attributes,
                'name' : name,
                'originalUrl': original_url,
                'thumbnailUrl': thumbnail_url,
                'dataPreviewUrl': dataPreviewUrl,
                'lockiUrl': lockiUrl,
                'url': url,
                **uri_dict  # This syntax merges the uri_dict into the result dictionary
            }
            continue
        # NFT with no assets - neither media try this out
        identifier = item.get('identifier', 'NFT without identifier')
        name = item.get('name','NFT without name')
        url = media.get('url', '')
        uris = item.get('uris', []) 
        uri_dict = {f'uri{i + 1}': decoded_uri for i, decoded_uri in enumerate(decoded_uris)}
        result[identifier]= {
                'name' : name,
                'url': url,
                **uri_dict  # This syntax merges the uri_dict into the result dictionary
            }
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
