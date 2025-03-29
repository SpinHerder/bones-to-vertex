bl_info = {
    "name": "Batch Vertex Rename",
    "author": "Spin Herder",
    "version": (0, 1),
    "blender": (4, 1, 0),
    "location": "3D View > Sidebar > Vertex Group Tools",
    "description": "Batch rename vertex groups to appropriate bones",
    "category": "Object",
}
import bpy

class VertexGroupMapItem(bpy.types.PropertyGroup):
    vg_name: bpy.props.StringProperty(name="Vertex Group")
    bone_name: bpy.props.StringProperty(name="Bone")

class VIEW3D_PT_VertexGroupRenamer(bpy.types.Panel):
    bl_label = "Vertex Group Renamer"
    bl_idname = "VIEW3D_PT_vertex_group_renamer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VG Renamer"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.label(text="Select Objects:")
        layout.prop_search(scene, "vg_armature", bpy.data, "objects", 
                          text="Armature", icon='ARMATURE_DATA')
        layout.prop_search(scene, "vg_mesh", bpy.data, "objects",
                          text="Mesh", icon='MESH_DATA')

        row = layout.row()
        row.enabled = bool(scene.vg_armature and scene.vg_mesh)
        row.operator("object.vg_start_mapping", 
                    text="Match groups to bones",
                    icon='MOD_ARMATURE')

        if scene.show_vg_mapping:
            self.draw_mapping_interface(context)

    def draw_mapping_interface(self, context):
        scene = context.scene
        layout = self.layout
        box = layout.box()
        
        scroll = box.box()
        
        split = scroll.split(factor=0.5)
        
        num_items = len(scene.vg_mapping_items)
        visible_count = 10
        start_idx = max(0, min(scene.vg_scroll_index, num_items - visible_count))
        end_idx = min(start_idx + visible_count, num_items)

        col = split.column()
        col.label(text="Vertex Groups:")
        for item in scene.vg_mapping_items[start_idx:end_idx]:
            col.label(text=item.vg_name)

        col = split.column()
        col.label(text="Map to Bones:")
        for item in scene.vg_mapping_items[start_idx:end_idx]:
            col.prop_search(item, "bone_name", 
                           scene.vg_armature.data, "bones", 
                           text="")

        row = box.row()
        if scene.vg_scroll_index > 0:
            row.operator("object.vg_scroll_up", text="Scroll up", icon='TRIA_UP')
        else:
            row.label(text="")
            
        if num_items > visible_count and end_idx < num_items:
            row.operator("object.vg_scroll_down", text="Scroll down", icon='TRIA_DOWN')
        else:
            row.label(text="")

        row = box.row()
        row.operator("object.vg_apply_mapping", text="Apply", icon='CHECKMARK')
        row.operator("object.vg_cancel_mapping", text="Cancel", icon='X')

class OBJECT_OT_ScrollUp(bpy.types.Operator):
    bl_idname = "object.vg_scroll_up"
    bl_label = "Scroll Up"
    
    def execute(self, context):
        context.scene.vg_scroll_index = max(0, context.scene.vg_scroll_index - 1)
        return {'FINISHED'}

class OBJECT_OT_ScrollDown(bpy.types.Operator):
    bl_idname = "object.vg_scroll_down"
    bl_label = "Scroll Down"
    
    def execute(self, context):
        context.scene.vg_scroll_index += 1
        return {'FINISHED'}

class OBJECT_OT_StartMapping(bpy.types.Operator):
    bl_idname = "object.vg_start_mapping"
    bl_label = "Start Vertex Group Mapping"
    
    def execute(self, context):
        scene = context.scene
        scene.show_vg_mapping = True
        scene.vg_scroll_index = 0
        
        scene.vg_mapping_items.clear()
        
        armature = scene.vg_armature
        mesh = scene.vg_mesh
        
        if armature and mesh:
            bone_names = {bone.name.lower(): bone.name 
                          for bone in armature.data.bones}
            
            for vg in mesh.vertex_groups:
                item = scene.vg_mapping_items.add()
                item.vg_name = vg.name
                lower_vg = vg.name.lower()
                item.bone_name = next(
                    (bn for ln, bn in bone_names.items() if ln in lower_vg),
                    ""
                )

        return {'FINISHED'}

class OBJECT_OT_ApplyMapping(bpy.types.Operator):
    bl_idname = "object.vg_apply_mapping"
    bl_label = "Apply Vertex Group Renaming"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        armature = scene.vg_armature
        mesh = scene.vg_mesh
        
        if not (armature and mesh):
            self.report({'ERROR'}, "Missing armature or mesh")
            return {'CANCELLED'}
        
        valid_bones = [bone.name for bone in armature.data.bones]
        renamed = 0
        
        for item in scene.vg_mapping_items:
            if item.bone_name in valid_bones:
                vg = mesh.vertex_groups.get(item.vg_name)
                if vg:
                    try:
                        vg.name = item.bone_name
                        renamed += 1
                    except:
                        pass 

        scene.show_vg_mapping = False
        self.report({'INFO'}, f"Renamed {renamed} vertex groups")
        return {'FINISHED'}

class OBJECT_OT_CancelMapping(bpy.types.Operator):
    bl_idname = "object.vg_cancel_mapping"
    bl_label = "Cancel Mapping"
    
    def execute(self, context):
        context.scene.show_vg_mapping = False
        return {'FINISHED'}

classes = (
    VertexGroupMapItem,
    VIEW3D_PT_VertexGroupRenamer,
    OBJECT_OT_StartMapping,
    OBJECT_OT_ApplyMapping,
    OBJECT_OT_CancelMapping,
    OBJECT_OT_ScrollUp,
    OBJECT_OT_ScrollDown,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.vg_armature = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE'
    )
    bpy.types.Scene.vg_mesh = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    bpy.types.Scene.vg_mapping_items = bpy.props.CollectionProperty(
        type=VertexGroupMapItem
    )
    bpy.types.Scene.show_vg_mapping = bpy.props.BoolProperty(
        default=False
    )
    bpy.types.Scene.vg_scroll_index = bpy.props.IntProperty(
        default=0
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.vg_armature
    del bpy.types.Scene.vg_mesh
    del bpy.types.Scene.vg_mapping_items
    del bpy.types.Scene.show_vg_mapping
    del bpy.types.Scene.vg_scroll_index

if __name__ == "__main__":
    register()