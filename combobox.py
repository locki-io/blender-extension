import bpy


bl_info = {
    "name": "comoboxTest",
    "description": "learn how work combobox in blender",
    "author": "zebus3d",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "wiki_url": "",
    "category": "3D View" 
}


def comboCanged(self, context):
    current = bpy.context.scene.comboBox
    print("change to: ", current)

def updateComboContent(cItems):
    if cItems:
        bpy.types.Scene.comboBox = bpy.props.EnumProperty(
            items=cItems,
            name="Items",
            description="Item",
            default=None,
            update=comboCanged
        )


def mySceneProperties():
    bpy.types.Scene.Iname = bpy.props.StringProperty( name = "", default = "", description = "Item Name")

    comboItems = [
        ("no_items", "No items", "", 1),
    ]
    updateComboContent(comboItems)


class myButton(bpy.types.Operator):
    bl_label = "Button"
    bl_idname = "b.action"
    bl_description = "My button"
    
    def execute(self, context):
        fp = bpy.context.blend_data.filepath
        bn = bpy.context.scene.Iname
        if bn:
            if fp:
                comboItems = [
                    ("anew", "Anew", "", 1),
                    ("bnew", "Bnew", "", 2),
                    ("cnew", "Cnew", "", 3),
                    ("no_items", "No items", "", 4),
                ]
                updateComboContent(comboItems)
                try:
                    bpy.context.scene.comboBox = bn
                except:
                    bpy.context.scene.comboBox = "no_items"
            else:
                self.report({'ERROR'}, 'It is necessary to first save your scene')
        else:
            self.report({'ERROR'}, 'Invalid name for Item')

        return {'FINISHED'}


class myPanel(bpy.types.Panel):
    bl_label = "ComboBox"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ComboBox"

    def draw(self, context):
        scn = bpy.context.scene
        layout = self.layout
        col = layout.column()
        col.prop(scn, "comboBox", text="")
        col.prop(scn, "Iname")
        col.operator("b.action", text="Add Item")


classes = (
    myButton,
    myPanel
)


def register():
    from bpy.utils import register_class

    mySceneProperties()

    for cls in classes:
        register_class(cls)
    
    # mySceneProperties()