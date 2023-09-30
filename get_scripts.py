import bpy

# Import home made scripts

def add_subdiv_monkey_obj(size, subdiv_viewport_levels, subdiv_render_levels, shade_smooth):
    bpy.ops.mesh.primitive_monkey_add(size=size)

    bpy.ops.object.modifier_add(type="SUBSURF")
    bpy.context.object.modifiers["Subdivision"].levels = subdiv_viewport_levels
    bpy.context.object.modifiers["Subdivision"].render_levels = subdiv_render_levels

    if shade_smooth:
        bpy.ops.object.shade_smooth()


class MESH_OT_add_subdiv_monkey(bpy.types.Operator):
    """Create a new monkey mesh object with a subdivision surf modifier and shaded smooth"""

    bl_idname = "mesh.add_subdiv_monkey"
    bl_label = "Add Subdivided Monkey Mesh Object"
    bl_options = {"REGISTER", "UNDO"}

    mesh_size: bpy.props.FloatProperty(
        name="Size",
        default=4.0,
        description="The size of the monkey",
    )

    subdiv_viewport_lvl: bpy.props.IntProperty(
        name="Subdiv Viewport",
        default=1,
        min=1,
        max=3,
        description="The Subdivision Levels applied in the Viewport",
    )

    subdiv_render_lvl: bpy.props.IntProperty(
        name="Subdiv Render",
        default=3,
        min=3,
        max=7,
        description="The Subdivision Levels applied during the Viewport",
    )

    shade_smooth: bpy.props.BoolProperty(
        name="Shade Smooth",
        default=True,
        description="Apply Smooth Shading to the mesh",
    )

    def execute(self, context):

        add_subdiv_monkey_obj(self.mesh_size, self.subdiv_viewport_lvl,
                              self.subdiv_render_lvl, self.shade_smooth)

        return {"FINISHED"}



