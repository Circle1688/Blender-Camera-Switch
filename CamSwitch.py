bl_info = {
    "name": "Camera Switch",
    "author": "Circle_Coder",
    "version": (1, 0),
    "blender": (4, 5, 0),
    "location": "3D Viewport > Header",
    "description": "快速切换相机视角",
    "category": "Camera",
}

import bpy
from bpy.types import Operator, Menu, Panel, PropertyGroup, PointerProperty, Object, IntProperty
import addon_utils

def update_render_resolution(cam, context):
    cam=context.scene.camera.data
    render = context.scene.render
   
    if cam.Res_Orientation == 'LANDSCAPE':
        if cam.Res_Preset != 'CUSTOM':
            render.resolution_x = cam.Res_X
            render.resolution_y = round(cam.Res_X * float(cam.Res_Preset.split(':')[1]) / float(cam.Res_Preset.split(':')[0]))
        else:
            render.resolution_x = cam.Res_X
            render.resolution_y = cam.Res_Y
    else:
        if cam.Res_Preset != 'CUSTOM':
            render.resolution_x = round(cam.Res_X * float(cam.Res_Preset.split(':')[1]) / float(cam.Res_Preset.split(':')[0]))
            render.resolution_y = cam.Res_X
        else:
            render.resolution_x = cam.Res_Y
            render.resolution_y = cam.Res_X

def update_resolution_percentage(cam, context):
    cam=context.scene.camera.data
    context.scene.render.resolution_percentage = cam.Res_Percent

def update_camera_notes(self,context):
    context.region.tag_redraw()

addon_keymaps = {}
bpy.types.Camera.Res_X = bpy.props.IntProperty(name="水平分辨率", min=1, default=1920, subtype="PIXEL", update=update_render_resolution)
bpy.types.Camera.Res_Y = bpy.props.IntProperty(name="垂直分辨率", min=1, default=1080, subtype="PIXEL", update=update_render_resolution)
bpy.types.Camera.Res_Percent = bpy.props.IntProperty(min=1, max=200, default=100, update=update_resolution_percentage)
bpy.types.Camera.camswitch_notes = bpy.props.StringProperty(name="Notes", default="点击铅笔图标可更改文本。\n输入 == 来换行。", update=update_camera_notes)
bpy.types.Camera.Res_Preset = bpy.props.EnumProperty(
    name="分辨率预设",
    items=[
        ('1:1', '1:1', '1:1 Aspect Ratio', 0, 0),
        ('3:2', '3:2', '3:2 Aspect Ratio', 0, 1),
        ('4:3', '4:3', '4:3 Aspect Ratio', 0 , 2),
        ('16:9', '16:9', '16:9 Aspect Ratio', 0, 3),
        ('2.35:1', '2.35:1', '2.35:1 Aspect Ratio', 0, 4),
        ('1.4142:1', 'ISO-A Paper', 'ISO-A Paper Ratio', 0, 5),
        ('CUSTOM', 'Custom Resolution', 'Custom Resolution', 0, 6),
    ],
    default='16:9',
    update=update_render_resolution,
)
bpy.types.Camera.Res_Orientation = bpy.props.EnumProperty(
    name="Resolution Orientation",
    items=[
        ('LANDSCAPE', 'Landscape', 'Landscape Orientation', 0),
        ('PORTRAIT', 'Portrait', 'Portrait Orientation', 1),
    ],
    default='LANDSCAPE',
    update=update_render_resolution,
)

def camswitch_user_keyconfig(key):
    km, kmi = addon_keymaps[key]
    for item in bpy.context.window_manager.keyconfigs.user.keymaps[km.name].keymap_items:
        found_item = False
        if kmi.idname == item.idname:
            found_item = True
            for name in dir(kmi.properties):
                if not name in ["bl_rna", "rna_type"] and not name[0] == "_":
                    if name in kmi.properties and name in item.properties and not kmi.properties[name] == item.properties[name]:
                        found_item = False
        if found_item:
            return item
    print(f"Couldn't find keymap item for {key}, using addon keymap instead. This won't be saved across sessions!")
    return kmi

class CAMSWITCH_PREFERENCES(bpy.types.AddonPreferences):
    bl_idname = __name__

    camswitch_int_property: bpy.props.IntProperty(
        name="CAMSWITCH_PANEL_WIDTH",
        default=10,
        min=8,
        max=24,
    )

    show_width_setting: bpy.props.BoolProperty(
        name="Display Panel Width Setting",
        default=False,
    )

    def draw(self, context):
        layout = self.layout 
        row=layout.row()
        row.label(text="Keyboard Shortcut:")
        row.prop(camswitch_user_keyconfig('895BD'), 'type', text='', full_event=True)
        
        row=layout.row(align=False)
        row.label(text="Panel Width:")
        row.prop(self, 'camswitch_int_property', text='', slider=False)

        row=layout.row()
        row.prop(self, 'show_width_setting', text="Display 'Panel Width' setting in the 3D Viewport panel")

class CAMSWITCH_OT_ADD(bpy.types.Operator):
    bl_idname = "camswitch.add_camera"
    bl_label = "Add Camera"
    bl_options = {"UNDO"}

    def execute(self, context):
        # Check if user is already in camera view if so don't do anything
        space = context.space_data
        if space.type == 'VIEW_3D' and space.region_3d is not None and space.region_3d.view_perspective == 'CAMERA':
            self.report({'WARNING'}, "Cannot add a new camera while in camera view. Please switch to 3D viewport.")
            return {"CANCELLED"}

        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Add camera only in Object Mode")
            return {'CANCELLED'}

        # Add new camera aligned to viewport view
        camera_data = bpy.data.cameras.new(name="Camera")
        if camera_data is None:
            return {"CANCELLED"}

        camswitch_camera = bpy.data.objects.new("Camera", camera_data)

        if camswitch_camera is None:
            return {"CANCELLED"}

        bpy.context.scene.collection.objects.link(camswitch_camera)
        context.scene.camera = camswitch_camera

        # Select and activate the added camera
        bpy.ops.object.select_all(action='DESELECT')
        camswitch_camera.select_set(True)
        context.view_layer.objects.active = camswitch_camera
        update_render_resolution(camswitch_camera, context)
        bpy.ops.view3d.camera_to_view()

        # Set viewport mode to perspective if not already in camera view
        if space.region_3d.view_perspective == 'ORTHO':
            bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

        return {"FINISHED"}

class CAMSWITCH_OT_FOCUSOBJECT(bpy.types.Operator):
    bl_idname = "camswitch.focus_object"
    bl_label = "Choose Focus Object"
    bl_options = {"UNDO"}

    def execute(self, context):
        camera = context.scene.camera

        if camera is None:
            self.report({'WARNING'}, "No active camera")
            return {'CANCELLED'}

        if not camera.data.dof.use_dof:
            self.report({'WARNING'}, "Turn on Depth of Field to add Focus Object")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = camera
        camera.data.dof.focus_object = None

        focus_obj = bpy.context.active_object
        if focus_obj is None:
            self.report({'WARNING'}, "No active object to use as focus object")
            return {'CANCELLED'}

        camera.data.dof.focus_object = focus_obj

        return {'FINISHED'}

class CAMSWITCH_OT_REMOVEFOCUS(bpy.types.Operator):
    bl_idname = "camswitch.remove_focus"
    bl_label = "移除焦点对象"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.context.scene.camera.data.dof.focus_object = None
        return {'FINISHED'}

class CAMSWITCH_OT_EDITNOTE(bpy.types.Operator):
    bl_idname = "camswitch.edit_note"
    bl_label = "编辑相机备注"
    bl_options = {"UNDO"}

    text: bpy.types.Camera.camswitch_notes
    
    def execute(self, context):
        context.scene.camera.data.camswitch_notes = "\n".join(self.text.split("=="))
        return {'FINISHED'}

    def invoke(self, context, event):
        cam = context.scene.camera
        self.text = cam.data.camswitch_notes
        return context.window_manager.invoke_props_dialog(self)

class CAMSWITCH_OT_SWAPRES(bpy.types.Operator):
    bl_idname = "camswitch.swap_res"
    bl_label = "改变方向"
    bl_options = {'UNDO'}

    def execute(self, context):
        cam = context.scene.camera
        if cam.data.Res_Orientation == 'LANDSCAPE':
            cam.data.Res_Orientation = 'PORTRAIT'
        else:
            cam.data.Res_Orientation = 'LANDSCAPE'
        update_render_resolution(cam, context)
        return {'FINISHED'}

class CAMSWITCH_OT_SWITCH(bpy.types.Operator):
    bl_idname = "camswitch.switch_camera"
    bl_label = "切换到相机视图"
    camera_name: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        camera = scene.objects.get(self.camera_name)

        if camera:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D' and area == context.area:
                    area.spaces.active.region_3d.view_perspective = 'CAMERA'
                    break
            context.space_data.camera = camera
            scene.camera = camera
            update_render_resolution(camera.data, context)
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class CAMSWITCH_OT_RENAME(bpy.types.Operator):
    bl_idname = "camswitch.rename_camera"
    bl_label = "重命名相机"

    camera_name: bpy.props.StringProperty()
    new_name: bpy.props.StringProperty(
        name="",
        default="",
        description="Enter a new name for the camera"
    )

    def invoke(self, context, event):
        self.new_name = context.scene.objects[self.camera_name].name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="", icon="CAMERA_DATA",)
        row.prop(self, "new_name")

    def execute(self, context):
        scene = context.scene
        camera = scene.objects.get(self.camera_name)

        if camera:
            if camera == scene.camera:
                context.area.tag_redraw()
            camera.name = self.new_name
            scene.camera = camera
            update_render_resolution(camera.data, context)
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class CAMSWITCH_OT_REMOVE(bpy.types.Operator):
    bl_idname = "camswitch.remove_camera"
    bl_label = "删除相机"
    bl_options  = {'UNDO'}

    camera_name: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        camera = scene.objects.get(self.camera_name)

        if camera:
            bpy.data.objects.remove(camera, do_unlink=True)
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class CAMSWITCH_OT_SELECT(bpy.types.Operator):
    bl_idname = "camswitch.select_camera"
    bl_label = "选择相机"

    camera_name: bpy.props.StringProperty()

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'WARNING'}, "Select camera only in Object Mode")
            return {'CANCELLED'}

        camera_obj = bpy.data.objects.get(self.camera_name)

        if camera_obj:
            bpy.ops.object.select_all(action='DESELECT')
            camera_obj.select_set(True)
            context.view_layer.objects.active = camera_obj

        return {'FINISHED'}

class CAMSWITCH_PT_PANEL(bpy.types.Panel):
    bl_idname = "CAMSWITCH_PT_PANEL"
    bl_label = "Cameras"
    bl_space_type = 'VIEW_3D'
    # bl_region_type = 'UI'
    bl_region_type = 'HEADER'
    # bl_category = "Cam Switch"

    def draw(self, context):
        layout = self.layout
        data = bpy.data
        scene = context.scene

        addon_prefs = context.preferences.addons[__name__].preferences
        layout.ui_units_x = addon_prefs.camswitch_int_property

        if addon_prefs.show_width_setting:
            row = layout.column(align=True)
            row.prop(addon_prefs, "camswitch_int_property", text='Panel Width', slider=False)
        else:
            row = layout.row(align=True)

        #Camera List minimized
        box = layout.box()
        # box.enabled = True if any(obj.type == 'CAMERA' for obj in scene.objects) else False
        row=box.row()
        row.prop(scene, "camswitch_cameralist", text="相机列表", icon='TRIA_RIGHT'
            if not scene.camswitch_cameralist else 'TRIA_DOWN',
            emboss=False)
        row.operator("camswitch.add_camera", text="", icon="ADD", emboss=False)

        #Camera List collection
        camera_collections = {}
        
        for collection in data.collections:
            cameras_in_collection = []
            for obj in collection.objects:
                if obj.type == 'CAMERA':
                    cameras_in_collection.append(obj)
            if cameras_in_collection:
                camera_collections[collection.name] = cameras_in_collection
        
        cameras_in_scene = []
        for obj in context.scene.collection.objects:
            if obj.type == 'CAMERA':
                cameras_in_scene.append(obj)

        if cameras_in_scene:
            camera_collections['Scene Collection'] = cameras_in_scene

        #Camera List when Camera
        if scene.camswitch_cameralist:
            if not any(obj.type == 'CAMERA' for obj in scene.objects):
                row = box.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="No camera found", icon='INFO')
            #List all cameras per collection
            for collection_name, cameras in camera_collections.items():
                row=box.column(align=True)
                row.alignment = 'CENTER'
                row.label(text=collection_name)
                
                for cam_obj in cameras:
                    op_icon = 'RESTRICT_SELECT_OFF' if cam_obj and context.object == cam_obj else 'RESTRICT_SELECT_ON'
                    cam_icon = 'RESTRICT_RENDER_OFF' if cam_obj and cam_obj == context.scene.camera else 'RESTRICT_RENDER_ON'
                    row3 = row.row(align=True)
                    row3.operator("camswitch.switch_camera", text=cam_obj.name, icon=cam_icon).camera_name = cam_obj.name
                    row3.operator("camswitch.rename_camera", text="", icon="OUTLINER_OB_FONT").camera_name = cam_obj.name
                    row3.operator("camswitch.select_camera", text="", icon=op_icon).camera_name = cam_obj.name
                    row3.separator()
                    row3.operator("camswitch.remove_camera", text="", icon='TRASH', emboss=False).camera_name = cam_obj.name
               
        #Active Camera Settings Panel
        cam = scene.camera
        box = layout.box()
        box.enabled = True if any(obj.type == 'CAMERA' for obj in scene.objects) and cam is not None else False
        box.prop(scene, "camswitch_quicksettings", text="当前激活相机设置", icon='TRIA_RIGHT'
            if not scene.camswitch_quicksettings else 'TRIA_DOWN',
            emboss=False)
        
        if scene.camswitch_quicksettings and cam is not None:
            if not any(obj.type == 'CAMERA' for obj in scene.objects):
                row = box.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="No camera found", icon='INFO')
            
            #Resolution Settings
            col=box.column()
            row=col.row(align=True)
            row.label(text="分辨率: " + str(int(scene.render.resolution_x * cam.data.Res_Percent / 100)) + "x" + str(int(scene.render.resolution_y * cam.data.Res_Percent / 100)))
            row.operator("camswitch.swap_res", text="", icon='ARROW_LEFTRIGHT')

            if cam.data.Res_Preset != 'CUSTOM':
                row=col.row()
                row.label(text="最长边:")
                row.prop(cam.data, "Res_X", text="")
            else:
                row=col.row(align=True)
                row.prop(cam.data, "Res_X", text="X")
                row.prop(cam.data, "Res_Y", text="Y")

            row=col.row(align=False)
            row.prop(cam.data, "Res_Preset", text="")
            row.prop(cam.data, "Res_Percent", text="%", slider=True)
        
            #Lens Settings
            box = layout.box()
            col = box.column()

            if cam.data.type == 'PERSP':
                if cam.data.lens_unit == 'MILLIMETERS':
                    row=col.row(align=True)
                    row.label(text='焦距:')
                    row.prop(cam.data, 'lens', text='')
                elif cam.data.lens_unit == 'FOV':
                    row=col.row(align=True)
                    row.label(text='视野范围:')
                    row.prop(cam.data, 'angle', text='')
                
            elif cam.data.type == 'ORTHO':
                row=col.row(align=True)
                row.label(text='Ortho Scale:')
                row.prop(cam.data, 'ortho_scale', text='')

            elif cam.data.type == 'PANO':
                col.label(text="检查相机属性中的全景设置", icon='INFO')
            
            row=col.row(align=True)
            row.label(text='移位 X, Y:')
            row.prop(cam.data, 'shift_x', text='X')
            row.prop(cam.data, 'shift_y', text='Y')

            row=col.row(align=True)
            row.label(text='裁剪:')
            row.prop(cam.data, 'clip_start', text='')
            row.prop(cam.data, 'clip_end', text='')

            row=col.row(align=True)
            row.label(text='高度/旋转:')
            row.prop(cam, 'location', text='', index=2)
            row.prop(cam, 'rotation_euler', text='', index=2)

            row=col.row(align=True)
            row.label(text='类型:')
            row.prop(cam.data, 'type', text='')
            
            # row=col.row(align=True)
            # row.label(text='Lens Unit:')
            # row.prop(bpy.context.scene.camera.data, 'lens_unit', text='')

            #Depth of Field
            box = layout.box()
            col=box.column()
            col.prop(cam.data.dof, 'use_dof', text='Depth of Field', toggle=True)
            
            if cam.data.dof.focus_object:
                col.active = cam.data.dof.use_dof
                col.label(text="焦点对象: " + cam.data.dof.focus_object.name)
            else:
                col.active = cam.data.dof.use_dof
                col.label(text="焦点对象: None")

            row=col.row(align=True)
            row.enabled = cam.data.dof.use_dof
            row.operator("camswitch.focus_object", text="选择焦点对象", icon='PIVOT_BOUNDBOX')
            row.operator("camswitch.remove_focus", text="", icon='X')

            row=col.row()
            row.enabled = cam.data.dof.focus_object is None and cam.data.dof.use_dof
            row.label(text='焦点距离:')
            row.prop(cam.data.dof, 'focus_distance', text='')

            row=col.row()
            row.enabled = cam.data.dof.use_dof
            row.label(text='光圈:')
            row.prop(cam.data.dof, 'aperture_fstop', text='')

            #Extras
            box = layout.box()
            col=box.column()
            row=col.row(align=True)
            row.active = cam.data.show_passepartout
            row.label(text='Passepartout')
            row.prop(cam.data, 'show_passepartout', text='')
            row.prop(cam.data, 'passepartout_alpha', text='')
            
            row=col.row()
            row.prop(cam.data, 'show_name', text='Name')
            row.prop(cam.data, 'show_composition_thirds')
            row.prop(cam.data, 'show_composition_center')
            
            #Custom Notes
            box = layout.box()
            col=box.column()
            row=col.row()
            row.label(text=scene.camera.name + " 的备注:")
            row.operator("camswitch.edit_note", text="", icon='GREASEPENCIL', emboss=False)
            for line in cam.data.camswitch_notes.splitlines():
                row=col.row()
                row.scale_y = 0.6
                row.label(text=line)
                 
def CAMSWITCH_TOOL_HEADER(self, context):
    layout = self.layout
    active_camera = context.scene.camera

    if active_camera:
        popover_text = active_camera.name
    else:
        popover_text = "No active camera"

    layout.popover(
        panel="CAMSWITCH_PT_PANEL",
        icon="CAMERA_DATA",
        text=popover_text,
    )

classes = [
    CAMSWITCH_PREFERENCES,
    CAMSWITCH_OT_ADD,
    CAMSWITCH_OT_FOCUSOBJECT,
    CAMSWITCH_OT_REMOVEFOCUS,
    CAMSWITCH_OT_EDITNOTE,
    CAMSWITCH_OT_SWAPRES,
    CAMSWITCH_OT_SWITCH,
    CAMSWITCH_OT_RENAME,
    CAMSWITCH_OT_REMOVE,
    CAMSWITCH_OT_SELECT,
    CAMSWITCH_PT_PANEL,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('wm.call_panel', 'Z', 'PRESS',
        ctrl=True, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'CAMSWITCH_PT_PANEL'
    kmi.properties.keep_open = True
    addon_keymaps['895BD'] = (km, kmi)

    bpy.types.Scene.camswitch_cameralist = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.camswitch_quicksettings = bpy.props.BoolProperty(default=False)
    bpy.types.VIEW3D_HT_tool_header.prepend(CAMSWITCH_TOOL_HEADER)
    # bpy.types.VIEW3D_HT_header.append(CAMSWITCH_HEADER)

def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.types.VIEW3D_HT_tool_header.remove(CAMSWITCH_TOOL_HEADER)
    # bpy.types.VIEW3D_HT_header.remove(CAMSWITCH_HEADER)
    del bpy.types.Scene.camswitch_quicksettings
    del bpy.types.Scene.camswitch_cameralist

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()