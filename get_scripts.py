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

# Function to create an array of cubes with a wireframe modifier
def create_wireframe_cube_array(center, num_cubes, radius, size, rotation):
    import math
    cube_array = []
    
    for i in range(num_cubes):
        angle_x = math.radians(360 / num_cubes * i)
        
        for j in range(num_cubes):
            angle_y = math.radians(360 / num_cubes * j)
            
            x = center[0] + radius * math.cos(angle_x) * math.cos(angle_y)
            y = center[1] + radius * math.cos(angle_x) * math.sin(angle_y)
            z = center[2] + radius * math.sin(angle_x)
            
            # Create a cube and add it to the array
            bpy.ops.mesh.primitive_cube_add(size=5, location=(x, y, z))
            cube = bpy.context.active_object
            
            # Create a wireframe modifier and set its properties
            bpy.ops.object.modifier_add(type='WIREFRAME')
            wireframe_modifier = cube.modifiers[-1]
            wireframe_modifier.use_replace = True
            wireframe_modifier.thickness = 0.05  # Adjust the wireframe thickness as needed
            
            # Create keyframes for the rotation of the cube
            bpy.context.view_layer.objects.active = cube
            cube.rotation_euler = (0, 0, 0)
            cube.keyframe_insert(data_path="rotation_euler", frame=1)
            
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = 360  # Adjust as needed
            
            for frame in range(1, bpy.context.scene.frame_end + 1):
                cube.rotation_euler.x = math.radians(rotation * frame)
                cube.rotation_euler.y = math.radians(rotation * frame)
                cube.keyframe_insert(data_path="rotation_euler", frame=frame)
            
            cube_array.append(cube)
    
    return cube_array

def add_rotating_cube_obj(center, num_cubes, radius, size, rotation):
    import math
     # Create the main rotating cube
    bpy.ops.mesh.primitive_cube_add(size=5, location=center)
    main_cube = bpy.context.active_object

    # Add a wireframe modifier to the main cube and set its properties
    bpy.ops.object.modifier_add(type='WIREFRAME')
    wireframe_modifier = main_cube.modifiers[-1]
    wireframe_modifier.use_replace = True
    wireframe_modifier.thickness = 0.05  # Adjust the wireframe thickness as needed

    # Set up rotation animation for the main cube
    bpy.context.view_layer.objects.active = main_cube
    main_cube.rotation_euler = center
    main_cube.keyframe_insert(data_path="rotation_euler", frame=1)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 360  # Adjust as needed

    for frame in range(1, bpy.context.scene.frame_end + 1):
        main_cube.rotation_euler.x = math.radians(rotation * frame)
        main_cube.rotation_euler.y = math.radians(rotation * frame)
        main_cube.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Create an array of 10 smaller cubes around the main cube
    num_cubes_outer = 10  # Number of smaller cubes in the outer array
    radius_outer = 5.0  # Radius of the outer array
    size_outer = 1  # Size of each smaller cube in the outer array

    # outer_cube_array = create_wireframe_cube_array(center, num_cubes, radius, size, rotation)

    # Update the scene
    bpy.context.view_layer.update()

    create_wireframe_cube_array(center=center, num_cubes=num_cubes_outer, radius=radius_outer, size=size_outer, rotation=rotation)

class MESH_OT_add_rotating_cube_obj(bpy.types.Operator):
    bl_idname = "mesh.add_rotating_cube"
    bl_label = "Add rotating cube Object"
    bl_options = {"REGISTER", "UNDO"}

    # def add_rotating_cube_obj(size, center, num_cubes, radius, rotation_speed_degrees):
    # add definition of variables
    size: bpy.props.FloatProperty(
        name="Size",
        default=1.0,
        description="The size of the cube",
    )

    center: bpy.props.IntVectorProperty(
        name="center",
        default=(0, 0, 0),
        description="The center of the scene", 
    )

    num_cubes: bpy.props.IntProperty(
        name="number of cubes",
        default=10,
        description="The number of cubes to display", 
    )
    
    radius: bpy.props.FloatProperty(
        name="radius",
        default= 5.0,
        description= "The radius of the outer cubes",
    )

    rotation: bpy.props.FloatProperty(
        name="rotation",
        default= 4,
        description= "rotation of the object",
    )

    def execute(self, context):

        add_rotating_cube_obj( self.center, self.num_cubes, self.size ,self.radius, self.rotation)
        bpy.ops.screen.animation_play()
        
        return {"FINISHED"}
