# UnDrew Edit Start : Differentiate from the base add-on.
bl_info = {
    "name": "FBX format - AHiT patch",
    # This is now displayed as the maintainer, so show the foundation.
    # "author": "Campbell Barton, Bastien Montagne, Jens Restemeier, @Mysteryem", # Original Authors
    "author": "Original add-on by: Blender Foundation. Modified by: UnDrew",
    "version": (5, 0, 0),
    "blender": (2, 81, 0),
    "location": "File > Import-Export",
    "description": "Modified FBX add-on; fixes some compatibility issues with AHiT",
    "warning": "",
    "doc_url": "https://github.com/Un-Drew/io_scene_fbx_patch_ahit",
    "support": 'COMMUNITY',
    "category": "Import-Export",
}
# UnDrew Edit End


if "bpy" in locals():
    import importlib
    # COMPAT ADD BEGIN
    if "fbx_api_compat" in locals():
        importlib.reload(fbx_api_compat)
    # COMPAT ADD END
    if "import_fbx" in locals():
        importlib.reload(import_fbx)
    if "export_fbx_bin" in locals():
        importlib.reload(export_fbx_bin)
    if "export_fbx" in locals():
        importlib.reload(export_fbx)


import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
)

# COMPAT ADD BEGIN
from . import fbx_api_compat as api_compat
# COMPAT ADD END

# COMPAT ADD BEGIN
if api_compat.HAS_IMPORT_HELPER_INVOKE_POPUP_FUNC:
# COMPAT ADD END
    from bpy_extras.io_utils import (
        poll_file_object_drop,
    )

# COMPAT ADD BEGIN
from dataclasses import dataclass, field
# NOTE: Obsolete since later versions of Python, but needed in 3.7.
from typing import Optional, List


@dataclass
class CompatPanelInfo:
    """
    Helper class for an IO property panel, which holds enough information to define it either as a layout panel (created
    using `bpy.types.UILayout.panel()`), or as a registerable panel (that extends `bpy.types.Panel`).

    To be compatible with importing via drag-n-drop or exporting from collections, the addon needs to use layout panels.
    But those are only available since 4.1, so this class needs to support both panel types for backwards-compatibility.

    The property-drawing functions (import_panel_include, export_main, etc.) have been modified to remove their reliance
    on `panel()`, keeping only the common drawing code of the panel's body. This class does rest of the work, like
    creating the panel, setting the right flags, setting up the header, give it a check-box if needed, etc.
    """

    try:
        from typing import Protocol
    except ImportError:
        # `Protocol` is preferred here because it allows giving the parameters names, while `Callable` does not.
        # But if we don't have a choice (current py ver < 3.8), just use `Callable`. :/
        from typing import Callable
        CompatPanelDrawType = Callable[[bpy.types.UILayout, bpy.types.Operator, bool], None]
        del Callable
    else:
        class CompatPanelDrawType(Protocol):
            def __call__(self, body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_brows: bool) -> None: ...
        del Protocol

    # Name that uniquely identifies this panel. It's later combined with `categ` in `draw_in_op()` or `make_PT_type()`,
    # so this only needs to be unique against the panels in this addon, at most.
    id_name: str
    # Display name of this panel. Rendered next to the panel's check-box, if there is one.
    label: str
    # Callback for drawing the panel's body, using the properties defined in the passed-in operator.
    draw: CompatPanelDrawType
    # Display these properties as if they were part of the parent layout (operator/panel).
    hide_header: bool = False
    # Whether this panel should begin collapsed.
    default_closed: bool = False
    # If not None, the name of the boolean property that will be used to draw a check-box next to the header. This will
    # also control the body's enabled state (normal/grayed out).
    header_prop_name: Optional[str] = None
    # Panels to nest within this one.
    sub_panels: Optional[List['CompatPanelInfo']] = None

    # UnDrew Add Start : Lambda determining if a panel as a whole is enabled (header + body). None means always enabled.
    from typing import Callable
    enabled_if: Optional[Callable[[bpy.types.Operator], bool]] = None
    del Callable
    # UnDrew Add End

    if api_compat.HAS_LAYOUT_PANELS:
        def draw_in_op(self, operator: bpy.types.Operator, \
                       layout: bpy.types.UILayout, categ: str, is_file_browser: bool) -> None:
            """
            Creates a layout panel according to self's fields, sets up the header, draws the body using self's callback,
            and draws sub-panels, if there are any.
            """
            if self.hide_header:
                body = layout
            else:
                header, body = layout.panel(categ + "_" + self.id_name, default_closed=self.default_closed)
                if self.header_prop_name:
                    header.use_property_split = False
                    header.prop(operator, self.header_prop_name, text="")
                header.label(text=self.label)
                # UnDrew Add Start
                if self.enabled_if is not None:
                    header.enabled = self.enabled_if(operator)
                # UnDrew Add End
            if body:
                if self.header_prop_name:
                    body.enabled = getattr(operator, self.header_prop_name)
                # UnDrew Add Start
                if self.enabled_if is not None and body.enabled:
                    body.enabled = self.enabled_if(operator)
                # UnDrew Add End
                self.draw(body, operator, is_file_browser)
                if self.sub_panels:
                    for sub_panel in self.sub_panels:
                        sub_panel.draw_in_op(operator, body, categ, is_file_browser)

        @classmethod
        def draw_all_in_op(cls, panels: List['CompatPanelInfo'], operator: bpy.types.Operator, \
                           context: bpy.types.Context, categ: str) -> None:
            """
            Helper function for drawing a list of panels in an operator's layout.
            """
            layout = operator.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            # Are we inside the File browser
            is_file_browser = context.space_data.type == 'FILE_BROWSER'

            for panel in panels:
                panel.draw_in_op(operator, layout, categ, is_file_browser)

    def make_PT_type(self, categ: str, only_visible_in_op: str, bl_parent_id: str = "FILE_PT_operator") -> type:
        """
        Defines a class extending `bpy.types.Panel` accodring to self's fields, defined to be nested in a file browser's
        properties panel, only when the active operator matches `only_visible_in_op`. `bl_parent_id` can be supplied
        to nest one panel into another. Note that this doesn't take sub-panels into account; see: `make_PT_types()`.

        NOTE: `only_visible_in_op` must use Blender's internal operator naming convention.
              E.g., instead of "categ_name.addon_name", use "CATEG_NAME_OP_addon_name". (Case sensitive!)
        """
        class_name = categ + "_PT_" + self.id_name

        @classmethod
        def panel_method_poll(cls, context):
            sfile = context.space_data
            operator = sfile.active_operator

            return operator.bl_idname == cls._only_visible_in_op

        def panel_method_draw_header(self, context):
            sfile = context.space_data
            operator = sfile.active_operator

            self.layout.prop(operator, self._panel_info.header_prop_name, text="")

            # UnDrew Add Start
            if self._panel_info.enabled_if is not None:
                self.layout.enabled = self._panel_info.enabled_if(operator)
            # UnDrew Add End

        def panel_method_draw(self, context):
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            sfile = context.space_data
            operator = sfile.active_operator

            if self._panel_info.header_prop_name:
                layout.enabled = getattr(operator, self._panel_info.header_prop_name)

            # UnDrew Add Start
            if self._panel_info.enabled_if is not None and layout.enabled:
                layout.enabled = self._panel_info.enabled_if(operator)
            # UnDrew Add End

            self._panel_info.draw(layout, operator, True)

        bl_options = set()
        if self.hide_header:
            bl_options.add('HIDE_HEADER')
        if self.default_closed:
            bl_options.add('DEFAULT_CLOSED')

        attrs = {
            'bl_idname': class_name,
            'bl_space_type': 'FILE_BROWSER',
            'bl_region_type': 'TOOL_PROPS',
            'bl_label': self.label,
            'bl_parent_id': bl_parent_id,
            'bl_options': bl_options,

            '_only_visible_in_op': only_visible_in_op,
            '_panel_info': self,

            # NOTE: Since these functions live in the class, they're effectively indistinguishable from methods.
            'poll': panel_method_poll,
            'draw': panel_method_draw,
        }

        if self.header_prop_name:
            attrs['draw_header'] = panel_method_draw_header

        return type(class_name, (bpy.types.Panel,), attrs)

    @classmethod
    def make_PT_types(cls, panels: List['CompatPanelInfo'], \
                      categ: str, only_visible_in_op: str, bl_parent_id: str = "FILE_PT_operator") -> List[type]:
        """
        Helper function for defining the classes for an operator's list of panels, defining sub_panels as well.
        """
        types = []
        for panel in panels:
            panel_type = panel.make_PT_type(categ, only_visible_in_op, bl_parent_id=bl_parent_id)
            types.append(panel_type)
            if panel.sub_panels:
                types.extend(cls.make_PT_types(panel.sub_panels, \
                                        categ, only_visible_in_op, bl_parent_id=panel_type.bl_idname))
        return types


COMPAT_PANELS_IMPORT: List[CompatPanelInfo] = []
COMPAT_PANELS_EXPORT: List[CompatPanelInfo] = []
# COMPAT ADD END


# UnDrew Add Start : PATCH DEFAULTS

# For vanilla behaviour, change this one to False
DEF_IMPORT_ROOT_AS_BONE = True
# For vanilla behaviour, change this one to False
DEF_IMPORT_SCALE_INHERITANCE = True
# For vanilla behaviour, change this one to True
DEF_IMPORT_CONNECT_CHILDREN = False
# For vanilla behaviour, change this one to 'ALWAYS'
DEF_IMPORT_FPS_RULE = 'IF_FOUND'
# For vanilla behaviour, change this one to False
DEF_IMPORT_CUSTOM_FPS_FIX = True
# For vanilla behaviour, change this one to False
DEF_IMPORT_ACTION_DOMAIN = True

# For vanilla behaviour, change this one to False
DEF_EXPORT_DONT_ADD_ARMATURE_BONE = True
# For vanilla behaviour, change this one to False
DEF_EXPORT_MATRIX_DOUBLE_PRECISION = False
# For vanilla behaviour, change this one to False
DEF_EXPORT_NLA_MODULAR_ANIM_SUPPORT = False
# For vanilla behaviour, change this one to False
DEF_EXPORT_NLA_FORCE_EXPORT = False
# For vanilla behaviour, change this one to False
DEF_EXPORT_NLA_ONLY_ANIMATE_OWNER = True
# For vanilla behaviour, change this one to False
DEF_EXPORT_REST_DEFAULT_POSE = True
# For vanilla behaviour, change this one to False
DEF_EXPORT_REMOVE_ANIM_OBJECT_PREFIX = True
# For vanilla behaviour, change this one to True
DEF_EXPORT_ADD_LEAF_BONES = False

# UnDrew Add End


@orientation_helper(axis_forward='-Z', axis_up='Y')
# UnDrew Edit Start : Avoid conflicts + custom tooltip.
class ImportFBX_patch_ahit(bpy.types.Operator, ImportHelper):
    """Load a FBX file, using the patched importer"""
    bl_idname = "import_scene.fbx_patch_ahit"
# UnDrew Edit End
    bl_label = "Import FBX - AHiT"  # UnDrew Edit : Clarity, especially with drag-n-drop support.
    bl_options = {'UNDO', 'PRESET'}

    _directory_and_files_options = {'HIDDEN'}
    # COMPAT ADD BEGIN
    if api_compat.HAS_PROPERTY_SKIP_PRESET_OPTION:
    # COMPAT ADD END
        _directory_and_files_options.add('SKIP_PRESET')

    directory: StringProperty(
        subtype='DIR_PATH',
        options=_directory_and_files_options,
    )

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        options=_directory_and_files_options,
    )

    ui_tab: EnumProperty(
        items=(('MAIN', "Main", "Main basic settings"),
               ('ARMATURE', "Armatures", "Armature-related settings"),
               ),
        name="ui_tab",
        description="Import options categories",
    )

    use_manual_orientation: BoolProperty(
        name="Manual Orientation",
        description="Specify orientation and scale, instead of using embedded data in FBX file",
        default=False,
    )
    global_scale: FloatProperty(
        name="Scale",
        min=0.001, max=1000.0,
        default=1.0,
    )
    bake_space_transform: BoolProperty(
        name="Apply Transform",
        description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
        "target space is not aligned with Blender's space "
        "(WARNING! experimental option, use at own risk, known to be broken with armatures/animations)",
        default=False,
    )

    use_custom_normals: BoolProperty(
        name="Custom Normals",
        description="Import custom normals, if available (otherwise Blender will recompute them)",
        default=True,
    )
    colors_type: EnumProperty(
        name="Vertex Colors",
        items=(('NONE', "None", "Do not import color attributes"),
               ('SRGB', "sRGB", "Expect file colors in sRGB color space"),
               ('LINEAR', "Linear", "Expect file colors in linear color space"),
               ),
        description="Import vertex color attributes",
        default='SRGB',
    )

    use_image_search: BoolProperty(
        name="Image Search",
        description="Search subdirs for any associated images (WARNING: may be slow)",
        default=True,
    )

    use_alpha_decals: BoolProperty(
        name="Alpha Decals",
        description="Treat materials with alpha as decals (no shadow casting)",
        default=False,
    )
    decal_offset: FloatProperty(
        name="Decal Offset",
        description="Displace geometry of alpha meshes",
        min=0.0, max=1.0,
        default=0.0,
    )

    use_anim: BoolProperty(
        name="Import Animation",
        description="Import FBX animation",
        default=True,
    )
    anim_offset: FloatProperty(
        name="Animation Offset",
        description="Offset to apply to animation during import, in frames",
        default=1.0,
    )
    # UnDrew Add Start : A way to skip importing the FPS.
    UE3_fps_import_rule: EnumProperty(
        name="UE3 - FPS import rule",
        items=(('ALWAYS', "Always import", "Vanilla behaviour - Always sets the FPS, defauts to 25 when not found"),
               ('IF_FOUND', "Only if found", "Only sets the FPS if it's defined in the FBX file, otherwise the existing one remains"),
               ('NEVER', "Never import", "Never imports or sets the FPS, so the existing one remains"),
               ),
        description="Defines in what situations should the FPS be imported and overwritten",
        default=DEF_IMPORT_FPS_RULE,
    )
    # UnDrew Add End
    # UnDrew Add Start : Time dilation fix when using Custom FPS.
    UE3_custom_fps_fix: BoolProperty(
        name="UE3 - Custom FPS fix",
        description="Fixes an oversight where the Base part of a custom frame rate would get ignored when importing animations",
        default=DEF_IMPORT_CUSTOM_FPS_FIX,
    )
    # UnDrew Add End
    # UnDrew Add Start : Fix for actions being created without initializing their id_root.
    UE3_set_action_id_root: BoolProperty(
        name="UE3 - Set action domains",
        description="Automatically makes imported actions only appear on the relevant Object/ID types. "
                    "Useful to avoid accidently locking an action to the wrong type later down the line",
        default=DEF_IMPORT_ACTION_DOMAIN,
    )
    # UnDrew Add End

    use_subsurf: BoolProperty(
        name="Subdivision Data",
        description="Import FBX subdivision information as subdivision surface modifiers",
        default=False,
    )

    use_custom_props: BoolProperty(
        name="Custom Properties",
        description="Import user properties as custom properties",
        default=True,
    )
    use_custom_props_enum_as_string: BoolProperty(
        name="Import Enums As Strings",
        description="Store enumeration values as strings",
        default=True,
    )

    ignore_leaf_bones: BoolProperty(
        name="Ignore Leaf Bones",
        description="Ignore the last bone at the end of each chain (used to mark the length of the previous bone)",
        default=False,
    )
    # UnDrew Add Start : Fix for Blender interpreting the root bone as the Armature.
    UE3_import_root_as_bone: BoolProperty(
        name="UE3 - Import Root as Bone",
        description="If enabled, the root bone is preserved for models exported from Unreal",
        default=DEF_IMPORT_ROOT_AS_BONE,
    )
    # UnDrew Add End
    # UnDrew Add Start : Support for importing scale inheritance (per-bone Inherit Scale property).
    UE3_import_scale_inheritance: BoolProperty(
        name="UE3 - Import Scale Inheritance",
        description="If enabled, the per-bone Inherit Scale property is correctly imported (AHiT always uses 'Aligned')",
        default=DEF_IMPORT_SCALE_INHERITANCE,
    )
    # UnDrew Add End
    # UnDrew Add Start : Option to toggle whether to try connecting bones on import.
    UE3_connect_children: BoolProperty(
        name="UE3 - Connect Children",
        description="If disabled, don't attempt to connect bones at all. "
                    "If enabled (vanilla), connect child bones if their position matches the parent's tail "
                    "(Note this can break translation animation sometimes)",
        default=DEF_IMPORT_CONNECT_CHILDREN,
    )
    # UnDrew Add End
    force_connect_children: BoolProperty(
        name="Force Connect Children",
        description="Force connection of children bones to their parent, even if their computed head/tail "
        "positions do not match (can be useful with pure-joints-type armatures)",
        default=False,
    )
    automatic_bone_orientation: BoolProperty(
        name="Automatic Bone Orientation",
        description="Try to align the major bone axis with the bone children",
        default=False,
    )
    primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='Y',
    )
    secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='X',
    )

    use_prepost_rot: BoolProperty(
        name="Use Pre/Post Rotation",
        description="Use pre/post rotation from FBX transform (you may have to disable that in some cases)",
        default=True,
    )
    mtl_name_collision_mode: EnumProperty(
        name="Material Name Collision",
        items=(("MAKE_UNIQUE", "Make Unique", "Import each FBX material as a unique Blender material"),
               ("REFERENCE_EXISTING", "Reference Existing",
               "If a material with the same name already exists, reference that instead of importing"),
               ),
        default='MAKE_UNIQUE',
        description="Behavior when the name of an imported material conflicts with an existing material",
    )

    def draw(self, context):
        # COMPAT EDIT BEGIN : See CompatPanelInfo.
        if api_compat.HAS_LAYOUT_PANELS:
            CompatPanelInfo.draw_all_in_op(COMPAT_PANELS_IMPORT, self, context, "FBX_patch_ahit")  # UnDrew Edit : categ
        # COMPAT EDIT END

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory", "ui_tab", "filepath", "files"))

        from . import import_fbx
        import os

        if self.files:
            ret = {'CANCELLED'}
            for file in self.files:
                path = os.path.join(self.directory, file.name)
                if import_fbx.load(self, context, filepath=path, **keywords) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return import_fbx.load(self, context, filepath=self.filepath, **keywords)

    # COMPAT ADD BEGIN
    if api_compat.HAS_IMPORT_HELPER_INVOKE_POPUP_FUNC:
    # COMPAT ADD END
        def invoke(self, context, event):
            return self.invoke_popup(context)


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def import_panel_include(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "use_custom_normals")
    body.prop(operator, "use_subsurf")
    body.prop(operator, "use_custom_props")
    sub = body.row()
    sub.enabled = operator.use_custom_props
    sub.prop(operator, "use_custom_props_enum_as_string")
    body.prop(operator, "use_image_search")
    # COMPAT ADD BEGIN
    if api_compat.HAS_MESH_COL_ATTRS_PROP and api_compat.HAS_COL_ATTR_SRGB_PROP:
    # COMPAT ADD END
        body.prop(operator, "colors_type")


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def import_panel_transform(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "global_scale")
    body.prop(operator, "decal_offset")
    row = body.row()
    row.prop(operator, "bake_space_transform")
    row.label(text="", icon='ERROR')
    body.prop(operator, "use_prepost_rot")


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def import_panel_transform_orientation(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.enabled = operator.use_manual_orientation
    body.prop(operator, "axis_forward")
    body.prop(operator, "axis_up")


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def import_panel_materials(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "mtl_name_collision_mode")


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def import_panel_animation(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.enabled = operator.use_anim
    body.prop(operator, "anim_offset")
    # UnDrew Add Start : A way to skip importing the FPS.
    body.prop(operator, "UE3_fps_import_rule")
    # UnDrew Add End
    # UnDrew Add Start : Time dilation fix when using Custom FPS.
    body.prop(operator, "UE3_custom_fps_fix")
    # UnDrew Add End
    # UnDrew Add Start : Fix for actions being created without initializing their id_root.
    body.prop(operator, "UE3_set_action_id_root")
    # UnDrew Add End


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def import_panel_armature(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "ignore_leaf_bones")
    # UnDrew Add Start : Option to toggle whether to try connecting bones on import.
    body.prop(operator, "UE3_connect_children")
    # UnDrew Add End
    body.prop(operator, "force_connect_children"),
    body.prop(operator, "automatic_bone_orientation"),
    sub = body.column()
    sub.enabled = not operator.automatic_bone_orientation
    sub.prop(operator, "primary_bone_axis")
    sub.prop(operator, "secondary_bone_axis")
    # UnDrew Add Start : Fix for Blender interpreting the root bone as the Armature.
    body.prop(operator, "UE3_import_root_as_bone")
    # UnDrew Add End
    # UnDrew Add Start : Support for importing scale inheritance (per-bone Inherit Scale property).
    body.prop(operator, "UE3_import_scale_inheritance")
    # UnDrew Add End


# COMPAT ADD BEGIN
COMPAT_PANELS_IMPORT = [
    CompatPanelInfo(id_name="import_include", label="Include", draw=import_panel_include),
    CompatPanelInfo(id_name="import_transform", label="Transform", draw=import_panel_transform, sub_panels = [
        CompatPanelInfo(id_name="import_transform_manual_orientation", label="Manual Orientation", \
                        draw=import_panel_transform_orientation, header_prop_name="use_manual_orientation"),
    ]),
    CompatPanelInfo(id_name="import_materials", label="Materials", draw=import_panel_materials, default_closed=True),
    CompatPanelInfo(id_name="import_animation", label="Animation", draw=import_panel_animation, default_closed=True, \
                    header_prop_name="use_anim"),
    CompatPanelInfo(id_name="import_armature", label="Armature", draw=import_panel_armature, default_closed=True),
]
# COMPAT ADD END


@orientation_helper(axis_forward='-Z', axis_up='Y')
# UnDrew Edit Start : Avoid conflicts + custom tooltip.
class ExportFBX_patch_ahit(bpy.types.Operator, ExportHelper):
    """Write a FBX file, using the patched exporter"""
    bl_idname = "export_scene.fbx_patch_ahit"
# UnDrew Edit End
    bl_label = "Export FBX - AHiT"  # UnDrew Edit : Clarity.
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection: BoolProperty(
        name="Selected Objects",
        description="Export selected and visible objects only",
        default=False,
    )
    use_visible: BoolProperty(
        name='Visible Objects',
        description='Export visible objects only',
        default=False
    )
    use_active_collection: BoolProperty(
        name="Active Collection",
        description="Export only objects from the active collection (and its children)",
        default=False,
    )
    collection: StringProperty(
        name="Source Collection",
        description="Export only objects from this collection (and its children)",
        default="",
    )
    global_scale: FloatProperty(
        name="Scale",
        description="Scale all data (Some importers do not support scaled armatures!)",
        min=0.001, max=1000.0,
        soft_min=0.01, soft_max=1000.0,
        default=1.0,
    )
    apply_unit_scale: BoolProperty(
        name="Apply Unit",
        description="Take into account current Blender units settings (if unset, raw Blender Units values are used as-is)",
        default=True,
    )
    apply_scale_options: EnumProperty(
        items=(('FBX_SCALE_NONE', "All Local",
                "Apply custom scaling and units scaling to each object transformation, FBX scale remains at 1.0"),
               ('FBX_SCALE_UNITS', "FBX Units Scale",
                "Apply custom scaling to each object transformation, and units scaling to FBX scale"),
               ('FBX_SCALE_CUSTOM', "FBX Custom Scale",
                "Apply custom scaling to FBX scale, and units scaling to each object transformation"),
               ('FBX_SCALE_ALL', "FBX All",
                "Apply custom scaling and units scaling to FBX scale"),
               ),
        name="Apply Scalings",
        description="How to apply custom and units scalings in generated FBX file "
        "(Blender uses FBX scale to detect units on import, "
        "but many other applications do not handle the same way)",
    )

    use_space_transform: BoolProperty(
        name="Use Space Transform",
        description="Apply global space transform to the object rotations. When disabled "
        "only the axis space is written to the file and all object transforms are left as-is",
        default=True,
    )
    bake_space_transform: BoolProperty(
        name="Apply Transform",
        description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
        "target space is not aligned with Blender's space "
        "(WARNING! experimental option, use at own risk, known to be broken with armatures/animations)",
        default=False,
    )

    object_types: EnumProperty(
        name="Object Types",
        options={'ENUM_FLAG'},
        items=(('EMPTY', "Empty", ""),
               ('CAMERA', "Camera", ""),
               ('LIGHT', "Lamp", ""),
               ('ARMATURE', "Armature", "WARNING: not supported in dupli/group instances"),
               ('MESH', "Mesh", ""),
               ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
               ),
        description="Which kind of object to export",
        default={'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
    )

    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones) - "
        "WARNING: prevents exporting shape keys",
        default=True,
    )
    use_mesh_modifiers_render: BoolProperty(
        name="Use Modifiers Render Setting",
        description="Use render settings when applying modifiers to mesh objects (DISABLED in Blender 2.8)",
        default=True,
    )
    _mesh_smooth_type_items = [
        ('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
        ('FACE', "Face", "Write face smoothing"),
        ('EDGE', "Edge", "Write edge smoothing"),
    ]
    # COMPAT ADD BEGIN
    if api_compat.HAS_SMOOTH_GROUPS_BOUNDARY_VERTICES_PARAM:
        _mesh_smooth_type_items.append(('SMOOTH_GROUP', "Smoothing Groups", "Write face smoothing groups"))
    # COMPAT ADD END
    mesh_smooth_type: EnumProperty(
        name="Smoothing",
        items=_mesh_smooth_type_items,
        description="Export smoothing information "
        "(prefer 'Normals Only' option if your target importer understands custom normals)",
        default='OFF',
    )
    colors_type: EnumProperty(
        name="Vertex Colors",
        items=(('NONE', "None", "Do not export color attributes"),
               ('SRGB', "sRGB", "Export colors in sRGB color space"),
               ('LINEAR', "Linear", "Export colors in linear color space"),
               ),
        description="Export vertex color attributes",
        default='SRGB',
    )
    prioritize_active_color: BoolProperty(
        name="Prioritize Active Color",
        description="Make sure active color will be exported first. Could be important "
        "since some other software can discard other color attributes besides the first one",
        default=False,
    )
    use_subsurf: BoolProperty(
        name="Export Subdivision Surface",
        description="Export the last Catmull-Rom subdivision modifier as FBX subdivision "
        "(does not apply the modifier even if 'Apply Modifiers' is enabled)",
        default=False,
    )
    use_mesh_edges: BoolProperty(
        name="Loose Edges",
        description="Export loose edges (as two-vertices polygons)",
        default=False,
    )
    use_tspace: BoolProperty(
        name="Tangent Space",
        description="Add binormal and tangent vectors, together with normal they form the tangent space "
        "(will only work correctly with tris/quads only meshes!)",
        default=False,
    )
    use_triangles: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles",
        default=False,
    )
    use_custom_props: BoolProperty(
        name="Custom Properties",
        description="Export custom properties",
        default=False,
    )
    add_leaf_bones: BoolProperty(
        name="Add Leaf Bones",
        description="Append a final bone to the end of each chain to specify last bone length "
        "(use this when you intend to edit the armature from exported data)",
        # UnDrew Edit Start : This is dumb and should be off by default :)
        default=DEF_EXPORT_ADD_LEAF_BONES # False for commit!
        # UnDrew Edit End
    )
    # UnDrew Add Start : Fix for Blender adding an extra root bone with the name of the Armature.
    UE3_dont_add_armature_bone: BoolProperty(
        name="UE3 - Don't Add Armature Bone",
        description="If enabled, armatures won't gain an extra root bone when imported into Unreal. "
                    "Necessary when creating models/animations for an existing skeletal structure",
        default=DEF_EXPORT_DONT_ADD_ARMATURE_BONE,
    )
    # UnDrew Add End
    # UnDrew Add Start : Matrix double precision.
    UE3_matrix_double_precision: BoolProperty(
        name="UE3 - Matrix Double Precision",
        description="Sometimes, bone rotations exported from Blender may look incorrect in other apps, likely "
                    "due to floating point precision issues. This setting exists to rebuild bone matrices using "
                    "double precision. This *may* fix that issue, although it's highly experimental!",
        default=DEF_EXPORT_MATRIX_DOUBLE_PRECISION,
    )
    # UnDrew Add End
    primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='Y',
    )
    secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='X',
    )
    use_armature_deform_only: BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=False,
    )
    armature_nodetype: EnumProperty(
        name="Armature FBXNode Type",
        items=(('NULL', "Null", "'Null' FBX node, similar to Blender's Empty (default)"),
               ('ROOT', "Root", "'Root' FBX node, supposed to be the root of chains of bones..."),
               ('LIMBNODE', "LimbNode", "'LimbNode' FBX node, a regular joint between two bones..."),
               ),
        description="FBX type of node (object) used to represent Blender's armatures "
        "(use the Null type unless you experience issues with the other app, "
        "as other choices may not import back perfectly into Blender...)",
        default='NULL',
    )
    bake_anim: BoolProperty(
        name="Baked Animation",
        description="Export baked keyframe animation",
        default=True,
    )
    bake_anim_use_all_bones: BoolProperty(
        name="Key All Bones",
        description="Force exporting at least one key of animation for all bones "
        "(needed with some target applications, like UE4)",
        default=True,
    )
    bake_anim_use_nla_strips: BoolProperty(
        name="NLA Strips",
        description="Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
        "instead of global scene animation",
        default=True,
    )
    bake_anim_use_all_actions: BoolProperty(
        name="All Actions",
        description="Export each action as a separated FBX's AnimStack, instead of global scene animation "
        "(note that animated objects will get all actions compatible with them, "
        "others will get no animation at all)",
        default=True,
    )
    bake_anim_force_startend_keying: BoolProperty(
        name="Force Start/End Keying",
        description="Always add a keyframe at start and end of actions for animated channels",
        default=True,
    )
    bake_anim_step: FloatProperty(
        name="Sampling Rate",
        description="How often to evaluate animated values (in frames)",
        min=0.01, max=100.0,
        soft_min=0.1, soft_max=10.0,
        default=1.0,
    )
    bake_anim_simplify_factor: FloatProperty(
        name="Simplify",
        description="How much to simplify baked values (0.0 to disable, the higher the more simplified)",
        min=0.0, max=100.0,  # No simplification to up to 10% of current magnitude tolerance.
        soft_min=0.0, soft_max=10.0,
        default=1.0,  # default: min slope: 0.005, max frame step: 10.
    )
    # UnDrew Add Start : Extended animation export properties.
    UE3_nla_modular_anim_support: BoolProperty(
        name="UE3 NLA - Modular Anim Support",
        description="If disabled (vanilla), NLA is exported on a per-strip basis. "
                    "If enabled, NLA is exported on a per-track basis, so multiple animations on the same row "
                    "will be exported, in full, as one single animation. Plus, additive animations placed above "
                    "will be merged down - rather than being individually exported",
        default=DEF_EXPORT_NLA_MODULAR_ANIM_SUPPORT,
    )
    UE3_nla_force_export: BoolProperty(
        name="UE3 NLA - Force Export",
        description="If disabled (vanilla), NLA tracks which are disabled are skipped during export. "
                    "If enabled, all NLA tracks will ALWAYS be exported",
        default=DEF_EXPORT_NLA_FORCE_EXPORT,
    )
    UE3_nla_only_animate_owner: BoolProperty(
        name="UE3 NLA - Only Animate Owner",
        description="If disabled (vanilla), NLA animations will bake the entire exported scene - even unrelated objects, which is unnecessary. "
                    "If enabled, these animations will only track their owner object",
        default=DEF_EXPORT_NLA_ONLY_ANIMATE_OWNER,
    )
    UE3_rest_default_pose: BoolProperty(
        name="UE3 - Rest Default Pose",
        description="If enabled, this causes the default pose in the FBX file to use the Rest Pose of the armature. "
                    "If disabled (vanilla), it uses the Current Pose. Enabling fixes a rare bug with AHiT, where animations "
                    "would've imported with an incorrectly multiplied scale, depending on the playhead's position",
        default=DEF_EXPORT_REST_DEFAULT_POSE,
    )
    UE3_remove_anim_object_prefix: BoolProperty(
        name="UE3 - Remove prefix from anim names",
        description="If enabled, this removes the object prefix from action names, which is normally added by the vanilla FBX add-on",
        default=DEF_EXPORT_REMOVE_ANIM_OBJECT_PREFIX,
    )
    # UnDrew Add End
    # UnDrew Add Start : Batch export Anims.
    UE3_batch_anims: BoolProperty(
        name="UE3 - Batch Export Anims",
        description="Exports all animations as separate FBX files, instead of putting them into the main file. "
                    "Necessary for UE3, which can't import animations from the same file with the right durations",
        default=False,
    )
    UE3_batch_skip_main: BoolProperty(
        name="Skip Main File",
        description="Skips exporting the main file, thus only saving the animation files",
        default=True,
    )
    UE3_batch_subpath: StringProperty(
        name="Sub-folder",
        description="The sub-folder in which the animation files will be exported. Leave this blank to export in the same folder as the main file",
        default="Anims",
    )
    UE3_batch_object_filter: EnumProperty(
        name="Object Filter",
        items=(('ALL', "Off (All Objects)", "No object filtering is present. Any objects found in the main file will be found in the animation files as well"),
               ('ONLY_OWNER', "Only Owner", "Each anim file only includes the object that owns said animation (usually an armature). \n"
                                            "NOTE: May prevent the file from opening in some programs (e.g. Microsoft 3D Viewer)"),
               ('ONLY_OWNER_AND_MESH', "Only Owner + Mesh", "Similar to 'Only Owner', but parented meshes are included as well"),
               ),
        default='ONLY_OWNER',
    )
    # UnDrew Add End
    path_mode: path_reference_mode
    embed_textures: BoolProperty(
        name="Embed Textures",
        description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
        default=False,
    )
    batch_mode: EnumProperty(
        name="Batch Mode",
        items=(('OFF', "Off", "Active scene to file"),
               ('SCENE', "Scene", "Each scene as a file"),
               ('COLLECTION', "Collection",
                "Each collection (data-block ones) as a file, does not include content of children collections"),
               ('SCENE_COLLECTION', "Scene Collections",
                "Each collection (including master, non-data-block ones) of each scene as a file, "
                "including content from children collections"),
               ('ACTIVE_SCENE_COLLECTION', "Active Scene Collections",
                "Each collection (including master, non-data-block one) of the active scene as a file, "
                "including content from children collections"),
               ),
    )
    use_batch_own_dir: BoolProperty(
        name="Batch Own Dir",
        description="Create a dir for each exported file",
        default=True,
    )
    use_metadata: BoolProperty(
        name="Use Metadata",
        default=True,
        options={'HIDDEN'},
    )

    def draw(self, context):
        # COMPAT EDIT BEGIN : See CompatPanelInfo.
        if api_compat.HAS_LAYOUT_PANELS:
            CompatPanelInfo.draw_all_in_op(COMPAT_PANELS_EXPORT, self, context, "FBX_patch_ahit")  # UnDrew Edit : categ
        # COMPAT EDIT END

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        from mathutils import Matrix
        if not self.filepath:
            raise Exception("filepath not set")

        global_matrix = (axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4()
                         if self.use_space_transform else Matrix())

        keywords = self.as_keywords(ignore=("check_existing",
                                            "filter_glob",
                                            "ui_tab",
                                            ))

        keywords["global_matrix"] = global_matrix

        from . import export_fbx_bin
        return export_fbx_bin.save(self, context, **keywords)


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def export_main(layout: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    row = layout.row(align=True)
    row.prop(operator, "path_mode")
    sub = row.row(align=True)
    sub.enabled = (operator.path_mode == 'COPY')
    sub.prop(operator, "embed_textures", text="", icon='PACKAGE' if operator.embed_textures else 'UGLYPACKAGE')
    if is_file_browser:
        row = layout.row(align=True)
        row.prop(operator, "batch_mode")
        sub = row.row(align=True)
        sub.prop(operator, "use_batch_own_dir", text="", icon='NEWFOLDER')


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def export_panel_include(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    # COMPAT ADD BEGIN
    if not api_compat.HAS_UI_LAYOUT_COLUMN_AND_ROW_HEADINGS:
        sublayout = body.column()
    else:
    # COMPAT ADD END
        sublayout = body.column(heading="Limit to")
    sublayout.enabled = (operator.batch_mode == 'OFF')
    if is_file_browser:
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_visible")
        sublayout.prop(operator, "use_active_collection")

    body.column().prop(operator, "object_types")
    body.prop(operator, "use_custom_props")


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def export_panel_transform(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "global_scale")
    body.prop(operator, "apply_scale_options")

    body.prop(operator, "axis_forward")
    body.prop(operator, "axis_up")

    body.prop(operator, "apply_unit_scale")
    body.prop(operator, "use_space_transform")
    row = body.row()
    row.prop(operator, "bake_space_transform")
    row.label(text="", icon='ERROR')


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def export_panel_geometry(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "mesh_smooth_type")
    body.prop(operator, "use_subsurf")
    body.prop(operator, "use_mesh_modifiers")
    #sub = body.row()
    # sub.enabled = operator.use_mesh_modifiers and False  # disabled in 2.8...
    #sub.prop(operator, "use_mesh_modifiers_render")
    body.prop(operator, "use_mesh_edges")
    body.prop(operator, "use_triangles")
    sub = body.row()
    # ~ sub.enabled = operator.mesh_smooth_type in {'OFF'}
    sub.prop(operator, "use_tspace")
    # COMPAT ADD BEGIN
    if api_compat.HAS_MESH_COL_ATTRS_PROP and api_compat.HAS_COL_ATTR_SRGB_PROP:
    # COMPAT ADD END
        body.prop(operator, "colors_type")
    body.prop(operator, "prioritize_active_color")


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def export_panel_armature(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.prop(operator, "primary_bone_axis")
    body.prop(operator, "secondary_bone_axis")
    body.prop(operator, "armature_nodetype")
    body.prop(operator, "use_armature_deform_only")
    body.prop(operator, "add_leaf_bones")
    # UnDrew Add Start : Fix for Blender adding an extra root bone with the name of the Armature.
    body.prop(operator, "UE3_dont_add_armature_bone")
    # UnDrew Add End
    # UnDrew Add Start : Matrix double precision.
    row = body.row()
    row.prop(operator, "UE3_matrix_double_precision")
    row.label(text="", icon='ERROR')
    # UnDrew Add End


# COMPAT EDIT BEGIN : See CompatPanelInfo.
def export_panel_animation(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
# COMPAT EDIT END
    body.enabled = operator.bake_anim
    body.prop(operator, "bake_anim_use_all_bones")
    body.prop(operator, "bake_anim_use_nla_strips")
    body.prop(operator, "bake_anim_use_all_actions")
    body.prop(operator, "bake_anim_force_startend_keying")
    body.prop(operator, "bake_anim_step")
    body.prop(operator, "bake_anim_simplify_factor")
    # UnDrew Add Start : Extended animation export properties.
    sublayout = body.column()
    sublayout.use_property_split = False  # These property names are pretty long, let's use all available space.
    sublayout.prop(operator, "UE3_nla_modular_anim_support")
    sublayout.prop(operator, "UE3_nla_force_export")
    sublayout.prop(operator, "UE3_nla_only_animate_owner")
    sublayout.prop(operator, "UE3_rest_default_pose")
    sublayout.prop(operator, "UE3_remove_anim_object_prefix")
    # UnDrew Add End


# UnDrew Add Start : Batch export Anims
def export_panel_UE3_batch_anims(body: bpy.types.UILayout, operator: bpy.types.Operator, is_file_browser: bool):
    body.prop(operator, "UE3_batch_skip_main")
    body.prop(operator, "UE3_batch_subpath")
    body.prop(operator, "UE3_batch_object_filter")
# UnDrew Add End


# COMPAT ADD BEGIN
COMPAT_PANELS_EXPORT = [
    CompatPanelInfo(id_name="export_main", label="", draw=export_main, hide_header=True),
    CompatPanelInfo(id_name="export_include", label="Include", draw=export_panel_include),
    CompatPanelInfo(id_name="export_transform", label="Transform", draw=export_panel_transform),
    CompatPanelInfo(id_name="export_geometry", label="Geometry", draw=export_panel_geometry, default_closed=True),
    CompatPanelInfo(id_name="export_armature", label="Armature", draw=export_panel_armature, default_closed=True),
    CompatPanelInfo(id_name="export_animation", label="Animation", draw=export_panel_animation, default_closed=True, \
                    header_prop_name="bake_anim"),
    # UnDrew Add Start : Batch export Anims
    CompatPanelInfo(id_name="export_UE3_batch_anims", label="UE3 - Batch Export Anims", \
                    draw=export_panel_UE3_batch_anims, default_closed=True, header_prop_name="UE3_batch_anims", \
                    enabled_if=lambda operator: operator.bake_anim),
    # UnDrew Add End
]
# COMPAT ADD END


# COMPAT ADD START
if api_compat.HAS_FILE_HANDLERS and api_compat.HAS_IMPORT_HELPER_INVOKE_POPUP_FUNC:
# COMPAT ADD END
    # UnDrew Edit Start : Avoid conflicts.
    class IO_FH_fbx_patch_ahit(bpy.types.FileHandler):
    # UnDrew Edit End
        bl_idname = "IO_FH_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.
        bl_label = "FBX - AHiT patch"  # UnDrew Edit : Clarity.
        bl_import_operator = "import_scene.fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.
        # COMPAT ADD START
        if api_compat.HAS_COLLECTION_EXPORTERS:
        # COMPAT ADD END
            bl_export_operator = "export_scene.fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.
        bl_file_extensions = ".fbx"

        @classmethod
        def poll_drop(cls, context):
            return poll_file_object_drop(context)


def menu_func_import(self, context):
    self.layout.operator(ImportFBX_patch_ahit.bl_idname, text="FBX - AHiT patch (.fbx)")  # UnDrew Edit : Clarity.


def menu_func_export(self, context):
    self.layout.operator(ExportFBX_patch_ahit.bl_idname, text="FBX - AHiT patch (.fbx)")  # UnDrew Edit : Clarity.


# UnDrew Edit Start : Avoid conflicts.
classes = []
classes.append(ImportFBX_patch_ahit)
# COMPAT ADD BEGIN
if not api_compat.HAS_LAYOUT_PANELS:
    classes.extend(CompatPanelInfo.make_PT_types(COMPAT_PANELS_IMPORT, "FBX_PATCH_AHIT", "IMPORT_SCENE_OT_fbx_patch_ahit"))
# COMPAT ADD END
classes.append(ExportFBX_patch_ahit)
# COMPAT ADD BEGIN
if not api_compat.HAS_LAYOUT_PANELS:
    classes.extend(CompatPanelInfo.make_PT_types(COMPAT_PANELS_EXPORT, "FBX_PATCH_AHIT", "EXPORT_SCENE_OT_fbx_patch_ahit"))
# COMPAT ADD END
# COMPAT ADD START
if api_compat.HAS_FILE_HANDLERS and api_compat.HAS_IMPORT_HELPER_INVOKE_POPUP_FUNC:
# COMPAT ADD END
    classes.append(IO_FH_fbx_patch_ahit)
# UnDrew Edit End


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
