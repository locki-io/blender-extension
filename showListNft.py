class ShowNftList(bpy.types.Operator):
    bl_idname = "object.show_nft_url_list"
    bl_label = "Show a message with a list of Nft url"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=400)

    def draw(self, context):
        import json
        layout = self.layout
        my_props = context.scene.my_tool

        #access data_string
        data_string = my_props.data_string
        data = json.loads(data_string)  # Convert string back to list        

        result = []
        for item in data:
            if 'media' in item and item['media']:
                identifier = item['identifier']
                media = item['media'][0]
                uris = item.get('uris', [])
                original_url = media.get('originalUrl', '')
                thumbnail_url = media.get('thumbnailUrl', '')
                url = media.get('url', '')
                uri_dict = {f'uri{i + 1}': uri for i, uri in enumerate(uris)}
                result.append({
                    'identifier': identifier,
                    'originalUrl': original_url,
                    'thumbnailUrl': thumbnail_url,
                    'url': url,
                    **uri_dict
                })

        for entry in result:
            info = f"Identifier: {entry['identifier']}"
            layout.label(text=info)
            info = f"Original URL: {entry['originalUrl']}"
            layout.label(text=info)
            info = f"Thumbnail URL: {entry['thumbnailUrl']}"
            layout.label(text=info)
            info = f"URL: {entry['url']}"
            layout.label(text=info)
            
            for key, value in entry.items():
                if key.startswith('uri'):
                    uri_info = f"{key}: {value}"
                    layout.label(text=uri_info)
