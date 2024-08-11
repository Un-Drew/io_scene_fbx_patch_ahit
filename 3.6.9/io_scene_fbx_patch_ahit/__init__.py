# SPDX-License-Identifier: GPL-2.0-or-later

# UnDrew Edit Start : Differentiate from the base add-on.
bl_info = {
    "name": "FBX format - AHiT patch",
    "author": "Original add-on by: Campbell Barton, Bastien Montagne, Jens Restemeier, @Mysteryem. Modified by: UnDrew",
    "version": (4, 2, 0),
    "blender": (3, 6, 0),
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


# UnDrew Add Start : PATCH DEFAULTS

# For vanilla behaviour, change this one to False
DEF_IMPORT_ROOT_AS_BONE = True
# For vanilla behaviour, change this one to False
DEF_IMPORT_SCALE_INHERITANCE = True
# For vanilla behaviour, change this one to 'ALWAYS'
DEF_IMPORT_FPS_RULE = 'IF_FOUND'
# For vanilla behaviour, change this one to False
DEF_IMPORT_CUSTOM_FPS_FIX = True

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
class ImportFBX(bpy.types.Operator, ImportHelper):
    # UnDrew Edit Start : Avoid conflicts + custom tooltip.
    """Load a FBX file, using the patched importer"""
    bl_idname = "import_scene.fbx_patch_ahit"
    # UnDrew Edit End
    bl_label = "Import FBX"
    bl_options = {'UNDO', 'PRESET'}

    directory: StringProperty()

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    files: CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
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

    def draw(self, context):
        pass

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory", "ui_tab", "filepath", "files"))

        from . import import_fbx
        import os

        if self.files:
            ret = {'CANCELLED'}
            dirname = os.path.dirname(self.filepath)
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if import_fbx.load(self, context, filepath=path, **keywords) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return import_fbx.load(self, context, filepath=self.filepath, **keywords)


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_import_include_patch_ahit(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_custom_normals")
        layout.prop(operator, "use_subsurf")
        layout.prop(operator, "use_custom_props")
        sub = layout.row()
        sub.enabled = operator.use_custom_props
        sub.prop(operator, "use_custom_props_enum_as_string")
        layout.prop(operator, "use_image_search")
        layout.prop(operator, "colors_type")


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_import_transform_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_scale")
        layout.prop(operator, "decal_offset")
        row = layout.row()
        row.prop(operator, "bake_space_transform")
        row.label(text="", icon='ERROR')
        layout.prop(operator, "use_prepost_rot")


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_import_transform_manual_orientation_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Manual Orientation"
    bl_parent_id = "FBX_PT_import_transform_ahit_patch"  # UnDrew Edit : Avoid conflicts.

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "use_manual_orientation", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.use_manual_orientation

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_import_animation_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "use_anim", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.use_anim

        layout.prop(operator, "anim_offset")
        # UnDrew Add Start : A way to skip importing the FPS.
        layout.prop(operator, "UE3_fps_import_rule")
        # UnDrew Add End
        # UnDrew Add Start : Time dilation fix when using Custom FPS.
        layout.prop(operator, "UE3_custom_fps_fix")
        # UnDrew Add End


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_import_armature_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Armature"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "ignore_leaf_bones")
        layout.prop(operator, "force_connect_children"),
        layout.prop(operator, "automatic_bone_orientation"),
        sub = layout.column()
        sub.enabled = not operator.automatic_bone_orientation
        sub.prop(operator, "primary_bone_axis")
        sub.prop(operator, "secondary_bone_axis")
        # UnDrew Add Start : Fix for Blender interpreting the root bone as the Armature.
        layout.prop(operator, "UE3_import_root_as_bone")
        # UnDrew Add End
        # UnDrew Add Start : Support for importing scale inheritance (per-bone Inherit Scale property).
        layout.prop(operator, "UE3_import_scale_inheritance")
        # UnDrew Add End


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportFBX(bpy.types.Operator, ExportHelper):
    # UnDrew Edit Start : Avoid conflicts + custom tooltip.
    """Write a FBX file, using the patched exporter"""
    bl_idname = "export_scene.fbx_patch_ahit"
    # UnDrew Edit End
    bl_label = "Export FBX"
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
    mesh_smooth_type: EnumProperty(
            name="Smoothing",
            items=(('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            description="Export smoothing information "
                        "(prefer 'Normals Only' option if your target importer understand split normals)",
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
        pass

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


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_export_main_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        row = layout.row(align=True)
        row.prop(operator, "path_mode")
        sub = row.row(align=True)
        sub.enabled = (operator.path_mode == 'COPY')
        sub.prop(operator, "embed_textures", text="", icon='PACKAGE' if operator.embed_textures else 'UGLYPACKAGE')
        row = layout.row(align=True)
        row.prop(operator, "batch_mode")
        sub = row.row(align=True)
        sub.prop(operator, "use_batch_own_dir", text="", icon='NEWFOLDER')


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_export_include_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        sublayout = layout.column(heading="Limit to")
        sublayout.enabled = (operator.batch_mode == 'OFF')
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_visible")
        sublayout.prop(operator, "use_active_collection")

        layout.column().prop(operator, "object_types")
        layout.prop(operator, "use_custom_props")


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_export_transform_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_scale")
        layout.prop(operator, "apply_scale_options")

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")

        layout.prop(operator, "apply_unit_scale")
        layout.prop(operator, "use_space_transform")
        row = layout.row()
        row.prop(operator, "bake_space_transform")
        row.label(text="", icon='ERROR')


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_export_geometry_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "mesh_smooth_type")
        layout.prop(operator, "use_subsurf")
        layout.prop(operator, "use_mesh_modifiers")
        #sub = layout.row()
        #sub.enabled = operator.use_mesh_modifiers and False  # disabled in 2.8...
        #sub.prop(operator, "use_mesh_modifiers_render")
        layout.prop(operator, "use_mesh_edges")
        layout.prop(operator, "use_triangles")
        sub = layout.row()
        #~ sub.enabled = operator.mesh_smooth_type in {'OFF'}
        sub.prop(operator, "use_tspace")
        layout.prop(operator, "colors_type")
        layout.prop(operator, "prioritize_active_color")


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_export_armature_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Armature"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "primary_bone_axis")
        layout.prop(operator, "secondary_bone_axis")
        layout.prop(operator, "armature_nodetype")
        layout.prop(operator, "use_armature_deform_only")
        layout.prop(operator, "add_leaf_bones")
        # UnDrew Add Start : Fix for Blender adding an extra root bone with the name of the Armature.
        layout.prop(operator, "UE3_dont_add_armature_bone")
        # UnDrew Add End
        # UnDrew Add Start : Matrix double precision.
        row = layout.row()
        row.prop(operator, "UE3_matrix_double_precision")
        row.label(text="", icon='ERROR')
        # UnDrew Add End


# UnDrew Edit Start : Avoid conflicts.
class FBX_PT_export_bake_animation_ahit_patch(bpy.types.Panel):
# UnDrew Edit End
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Bake Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"  # UnDrew Edit : Avoid conflicts.

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "bake_anim", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.bake_anim
        layout.prop(operator, "bake_anim_use_all_bones")
        layout.prop(operator, "bake_anim_use_nla_strips")
        layout.prop(operator, "bake_anim_use_all_actions")
        layout.prop(operator, "bake_anim_force_startend_keying")
        layout.prop(operator, "bake_anim_step")
        layout.prop(operator, "bake_anim_simplify_factor")
        # UnDrew Add Start : Extended animation export properties.
        sublayout = layout.column()
        sublayout.use_property_split = False  # These property names are pretty long, let's use all available space.
        sublayout.prop(operator, "UE3_nla_modular_anim_support")
        sublayout.prop(operator, "UE3_nla_force_export")
        sublayout.prop(operator, "UE3_nla_only_animate_owner")
        sublayout.prop(operator, "UE3_rest_default_pose")
        sublayout.prop(operator, "UE3_remove_anim_object_prefix")
        # UnDrew Add End


# UnDrew Add Start : Batch export Anims
class FBX_PT_export_UE3_batch_anims_ahit_patch(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "UE3 - Batch Export Anims"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_fbx_patch_ahit"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "UE3_batch_anims", text="")
        self.layout.enabled = operator.bake_anim

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.bake_anim and operator.UE3_batch_anims
        layout.prop(operator, "UE3_batch_skip_main")
        layout.prop(operator, "UE3_batch_subpath")
        layout.prop(operator, "UE3_batch_object_filter")
# UnDrew Add End


def menu_func_import(self, context):
    self.layout.operator(ImportFBX.bl_idname, text="FBX - AHiT patch (.fbx)")  # UnDrew Edit : Clarity.


def menu_func_export(self, context):
    self.layout.operator(ExportFBX.bl_idname, text="FBX - AHiT patch (.fbx)")  # UnDrew Edit : Clarity.


classes = (
    ImportFBX,
    # UnDrew Edit Start : Avoid conflicts.
    FBX_PT_import_include_patch_ahit,
    FBX_PT_import_transform_ahit_patch,
    FBX_PT_import_transform_manual_orientation_ahit_patch,
    FBX_PT_import_animation_ahit_patch,
    FBX_PT_import_armature_ahit_patch,
    # UnDrew Edit End
    ExportFBX,
    # UnDrew Edit Start : Avoid conflicts.
    FBX_PT_export_main_ahit_patch,
    FBX_PT_export_include_ahit_patch,
    FBX_PT_export_transform_ahit_patch,
    FBX_PT_export_geometry_ahit_patch,
    FBX_PT_export_armature_ahit_patch,
    FBX_PT_export_bake_animation_ahit_patch,
    # UnDrew Edit End
    # UnDrew Add Start : Batch export Anims
    FBX_PT_export_UE3_batch_anims_ahit_patch,
    # UnDrew Add End
)


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
