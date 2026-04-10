"""This module does various tasks related to checking/using the available API features of the current ver of Blender.

Many of Blender's major & minor updates have introduced a bunch of API changes. For some of these, the FBX python addon
had to be updated to support/leverage that new API.

Since that addon was normally bundled with Blender, there was (presumably) no incentive for the Blender developers to
make it backwards-compatible with APIs in older versions. However, because this project aims to be backwards-compatible,
some API calls need to be done conditionally.

As such, this module does the following:

* Keeps track of which API features are available.
* Sometimes, provides functions that conditionally use the appropriate API.
"""

import bpy
import bpy_extras.node_shader_utils
import bpy_extras.io_utils
import sys
import numpy as np

__author__ = "UnDrew"

PY_VER = sys.version_info
NUMPY_VER = tuple(int(x, 10) for x in np.__version__.split('.'))

def cycle_to_num(cycle):
    if cycle == 'alpha':
        return 0
    elif cycle == 'beta':
        return 1
    elif cycle == 'rc':
        return 2
    else:
        # Even if this isn't 'release', assume it anyway, as there could be Extra Secret cylce vals I'm not aware of. :S
        return 3

BL_VER_MAJOR, BL_VER_MINOR, BL_VER_MICRO = bpy.app.version
BL_VER_CYCLE = cycle_to_num(bpy.app.version_cycle)

def check_ver(min_major, min_minor, min_micro, min_cycle, tie_breaker_func=None):
    if BL_VER_MAJOR > min_major:
        return True
    if BL_VER_MAJOR < min_major:
        return False
    if BL_VER_MINOR > min_minor:
        return True
    if BL_VER_MINOR < min_minor:
        return False
    if BL_VER_MICRO > min_micro:
        return True
    if BL_VER_MICRO < min_micro:
        return False
    if BL_VER_CYCLE > cycle_to_num(min_cycle):
        return True
    if BL_VER_CYCLE < cycle_to_num(min_cycle):
        return False
    return tie_breaker_func and tie_breaker_func()

"""
Functions that check a class's props/funcs by name. This script uses these to find out which APIs are available.

Motivation:

A naive way to check whether an API is available would be to rely on the current Blender version. This works fine for
official Blender releases, but wouldn't always be correct on pre-release builds. It's not uncommon for a property to be
changed or replaced in the middle of a release cycle, so to support this, a more concrete check is needed.

Fortunately, both Python and Blender's RNA system allow you, from the class alone, to explicitly check for props/funcs.

Doing this is much safer than relying on the version alone, and should (hopefully) make it compatible with any daily
build that was made during that ver's development.

Why stop here:

A safer (and technically more correct) approach would've been to check the instances at runtime, using exceptions.
However, doing this for every instance would risk slowing the addon down, which I didn't want to do.

In contrast, checking the class guarantees me that the result will be consistent throughout the process's lifetime,
which in turn allows me to cache the result here. Also, personally, I think it's more readable this way.
"""

# Checks whether a module has the specified type or function.
def module_has_type_or_func(module, typeorfuncname):
    return hasattr(module, typeorfuncname)

# Checks whether a natively-defined class has the specified RNA property.
# Adapted from: https://blender.stackexchange.com/a/300562
def class_has_rna_prop(cla, propname):
    return propname in cla.bl_rna.properties

# Checks whether a class's RNA property is readonly.
# NOTE: For a full list of all of a propery's attributes, run: print(dir(cla.bl_rna.properties[propname]))
def class_rna_prop_is_readonly(cla, propname):
    return cla.bl_rna.properties[propname].is_readonly

# Checks whether a natively-defined class has the specified RNA function.
def class_has_rna_func(cla, funcname):
    return funcname in cla.bl_rna.functions

# Checks whether a class's RNA function has the specified parameter defined.
def class_rna_func_has_param(cla, funcname, paramname):
    return paramname in cla.bl_rna.functions[funcname].parameters

# Checks whether a class's RNA function's parameter is an output (return).
def class_rna_func_param_is_output(cla, funcname, paramname):
    return cla.bl_rna.functions[funcname].parameters[paramname].is_output

# Checks whether a class has the specified python-defined property (not to be confused with python attributes).
# NOTE: Sometimes, this is also applicable to natively-defined classes, because they're partially defined in Python.
#       See: https://projects.blender.org/blender/blender/src/tag/v5.0.0/scripts/modules/_bpy_types.py
def class_has_py_prop(cla, propname):
    return hasattr(cla, propname)

# Checks whether a class has the specified python-defined function.
def class_has_py_func(cla, funcname):
    return hasattr(cla, funcname)

# Checks whether bpy.types.bpy_struct has the specified RNA function.
# XXX: This is separate from class_has_rna_func() because bpy_struct seems to be special and doesn't have bl_rna.
#      Instead, its natively-defined functions are structured similarly to python-defined functions. Idk why?
def bpy_struct_has_rna_func(funcname):
    return hasattr(bpy.types.bpy_struct, funcname)

"""
Added in 2.90.0
Source: https://developer.blender.org/docs/release_notes/2.90/python_api/#user-interface
"""

HAS_UI_LAYOUT_COLUMN_AND_ROW_HEADINGS = class_rna_func_has_param(bpy.types.UILayout, 'column', 'heading')
HAS_FOREACH_SET_ENUM_SUPPORT = check_ver(2, 90, 0, 'beta')  # unsure how to check this more concretely...

"""
Added in 2.91.0
Sources:
    * https://developer.blender.org/docs/release_notes/2.91/python_api/#other-changes
    * https://developer.blender.org/docs/release_notes/2.91/modeling/#subdivision-surfaces
    * https://developer.blender.org/docs/release_notes/2.91/python_api/#compatibility
"""

HAS_MESH_ATTRIBUTES = class_has_rna_prop(bpy.types.Mesh, 'attributes')
HAS_VRTX_COLS_AS_ATTRS = HAS_MESH_ATTRIBUTES
HAS_SUBSURF_BOUNDARY_SMOOTH = class_has_rna_prop(bpy.types.SubsurfModifier, 'boundary_smooth')
HAS_BSDF_EMISSION_STRENGTH = class_has_py_prop(bpy_extras.node_shader_utils.PrincipledBSDFWrapper, 'emission_strength')

"""
Added in 2.93.0
Sources:
    * https://developer.blender.org/docs/release_notes/2.93/python_api/#python-39
    * https://docs.python.org/3/whatsnew/3.8.html
"""

# The := operator (commonly called "walrus operator") was only added in Python 3.8, so it can't be used in Blender
# versions before 2.93. Despite adding this condition here, I won't be using the operator at all, because Python seems
# to validate a whole script's syntax ahead of time.
HAS_PY_WALRUS = (PY_VER >= (3, 8))

"""
Added in 3.0.0
Sources:
    * https://developer.blender.org/docs/release_notes/3.0/python_api/#idproperty-ui-data-api
    * https://docs.blender.org/api/2.93/bpy.types.Object.html#bpy.types.Object.cycles_visibility
    * https://docs.blender.org/api/3.0/bpy.types.Object.html#bpy.types.Object.visible_shadow
"""

HAS_NUMPY_CONCATENATE_DTYPE_PARAM = (NUMPY_VER >= (1, 20))
HAS_REFACTORED_UI_DATA = bpy_struct_has_rna_func('id_properties_ui')
HAS_REFACTORED_VISIBLE_FLAGS = class_has_rna_prop(bpy.types.Object, 'visible_shadow')

"""
Added in 3.1.0
Source: https://developer.blender.org/docs/release_notes/3.1/python_api/#other-additions
"""

HAS_VRTX_AND_PLGN_NORM_ARRAYS = class_has_rna_prop(bpy.types.Mesh, 'vertex_normals')
# The match statement (called "switch" in other langs) was only added in Python 3.10, so it can't be used in Blender
# versions before 3.1. Despite adding this condition here, I won't be using the statement at all, because Python seems
# to validate a whole script's syntax ahead of time.
HAS_PY_MATCH = (PY_VER >= (3, 10))

"""
Added in 3.2.0
Sources:
    * https://developer.blender.org/docs/release_notes/3.2/sculpt/#color-attributes
    * https://docs.blender.org/api/3.2/change_log.html#bpy-types-mesh
"""

HAS_MESH_COL_ATTRS_PROP = class_has_rna_prop(bpy.types.Mesh, 'color_attributes')  # Also when the UI for them changed

"""
Added in 3.4.0
Sources:
    * https://docs.blender.org/api/3.4/change_log.html#bpy-types-bytecolorattributevalue
    * https://docs.blender.org/api/3.4/change_log.html#bpy-types-floatcolorattributevalue
    * https://developer.blender.org/docs/release_notes/3.4/python_api/#internal-mesh-format
"""

HAS_COL_ATTR_SRGB_PROP = HAS_VRTX_COLS_AS_ATTRS and class_has_rna_prop(bpy.types.ByteColorAttributeValue, 'color_srgb')
HAS_MESH_ATTR_MATERIAL_INDEX = check_ver(3, 4, 0, 'beta')  # unsure how to check this more concretely...
# NOTE: - This added `Mesh.has_crease_edge` at same time.
#       - This still remains True even after `HAS_REFACTORED_EDGE_CREASES_4_0` (see below).
HAS_REFACTORED_EDGE_CREASES_3_4 = class_has_rna_prop(bpy.types.Mesh, 'edge_creases')

"""
Added in 3.5.0
Source: https://developer.blender.org/docs/release_notes/3.5/python_api/#internal-mesh-format
"""

HAS_MESH_ATTR_POSITION = check_ver(3, 5, 0, 'beta')  # unsure how to check this more concretely...
HAS_MESH_ATTR_SHARP_EDGE = check_ver(3, 5, 0, 'beta')  # unsure how to check this more concretely...
HAS_UV_LAYER_UV_PROP = class_has_rna_prop(bpy.types.MeshUVLoopLayer, 'uv')

"""
Added in 3.6.0
Sources:
* https://developer.blender.org/docs/release_notes/3.6/python_api/#internal-mesh-format
* https://docs.blender.org/api/3.6/change_log.html#bpy-types-mesh
"""

HAS_REFACTORED_POLYS_FOR_CONSISTENT_ORDER_WITH_LOOPS = class_rna_prop_is_readonly(bpy.types.MeshPolygon, 'loop_total')
HAS_MESH_ATTR_SHARP_FACE = check_ver(3, 6, 0, 'beta')  # unsure how to check this more concretely...
HAS_MESH_ATTRS_CORNER_VERT_AND_CORNER_EDGE = check_ver(3, 6, 0, 'beta')  # unsure how to check this more concretely...
HAS_MESH_ATTR_EDGE_VERTS = check_ver(3, 6, 0, 'beta')  # unsure how to check this more concretely...
HAS_CORN_NORM_ARRAY = class_has_rna_prop(bpy.types.Mesh, 'corner_normals')

"""
Added in 4.0.0
Source: https://developer.blender.org/docs/release_notes/4.0/python_api/#mesh
"""

HAS_REFACTORED_EDGE_CREASES_4_0 = class_has_py_prop(bpy.types.Mesh, 'edge_creases')
if HAS_REFACTORED_EDGE_CREASES_4_0:
    HAS_REFACTORED_EDGE_CREASES_3_4 = True
HAS_REMOVED_MESH_CALC_NORMALS_FUNC = not class_has_rna_func(bpy.types.Mesh, 'calc_normals')

"""
Added in 4.1.0
Sources:
    * https://developer.blender.org/docs/release_notes/4.1/python_api/#mesh
    * https://docs.blender.org/api/4.1/change_log.html#bpy-types-mesh
    * https://developer.blender.org/docs/release_notes/4.1/python_api/#additions
    * https://developer.blender.org/docs/release_notes/4.1/python_api/#layout-panels
    * https://developer.blender.org/docs/release_notes/4.1/pipeline_assets_io/#new-file-handler-api
    * https://projects.blender.org/blender/blender/commit/992ec6487b
    * https://docs.blender.org/api/4.0/bpy_types_enum_items/property_flag_items.html#rna-enum-property-flag-items
    * https://docs.blender.org/api/4.1/bpy_types_enum_items/property_flag_items.html#rna-enum-property-flag-items
    * https://docs.blender.org/api/4.0/bpy.app.translations.html
    * https://docs.blender.org/api/4.1/bpy.app.translations.html#bpy.app.translations.pgettext_rpt
"""

# Several things happened in the same PR:
#    * Removed use_auto_smooth and auto_smooth_angle, replaced by new modifier
#    * Removed create_normals_split(), calc_normals_split() and free_normals_split()
#    * Made MeshLoop.normal readonly
#    * Added readonly normals_domain prop
#    * Added set_sharp_from_angle() which rewrites the 'sharp_edge' attr when called.
HAS_REFACTORED_MESH_SMOOTHING = not class_has_rna_prop(bpy.types.Mesh, 'use_auto_smooth')
HAS_SHAPEKEY_POINTS_PROP = class_has_rna_prop(bpy.types.ShapeKey, 'points')
# This was split into 3 PRs, so make sure you check for the latest format.
HAS_LAYOUT_PANELS = class_has_rna_func(bpy.types.UILayout, 'panel') \
                            and class_rna_func_has_param(bpy.types.UILayout, 'panel', 'layout_header') \
                            and class_rna_func_param_is_output(bpy.types.UILayout, 'panel', 'layout_header')
HAS_FILE_HANDLERS = module_has_type_or_func(bpy.types, 'FileHandler')
HAS_EXTENDED_DNA_TYPES_4_1 = check_ver(4, 1, 0, 'beta')  # unsure how to check this more concretely...
HAS_PROPERTY_SKIP_PRESET_OPTION = class_has_rna_prop(bpy.types.Property, 'is_skip_preset')
HAS_TRANSLATION_FOR_REPORTS = module_has_type_or_func(bpy.app.translations, 'pgettext_rpt')

"""
Added in 4.2.0
Source: https://developer.blender.org/docs/release_notes/4.2/python_api/#exporters
"""

# NOTE: This also adds `bpy_extras.io_utils.poll_file_object_drop()`
HAS_IMPORT_HELPER_INVOKE_POPUP_FUNC = class_has_py_func(bpy_extras.io_utils.ImportHelper, 'invoke_popup')
HAS_COLLECTION_EXPORTERS = HAS_FILE_HANDLERS and class_has_rna_prop(bpy.types.FileHandler, 'bl_export_operator')
# NOTE: There's a commit during 4.2's beta for explicitly removing `bl_info` from any extension module. I don't know if
#       extensions were fully functional at this point, but for my purposes it's enough.
HAS_EXTENSION_SUPPORT = check_ver(4, 2, 0, 'beta')
if HAS_EXTENSION_SUPPORT:
    assert(PY_VER >= (3, 11))
_ANIM_LAYERED_1_EXPERIMENTAL = check_ver(4, 2, 0, 'alpha') \
                                    and class_has_rna_prop(bpy.types.PreferencesExperimental, 'use_animation_baklava')

"""
Added in 4.3.0
Sources:
 * https://developer.blender.org/docs/release_notes/4.3/python_api/#attributes
 * https://projects.blender.org/blender/blender/commit/1939eb03a7b0e78828888797c6e7371cdafdc044
"""

HAS_SPECIALIZED_ATTR_GROUP_TYPES = module_has_type_or_func(bpy.types, 'AttributeGroupMesh')
HAS_CPP_NORMAL_NORMALIZATION = check_ver(4, 3, 0, 'beta')  # unsure how to check this more concretely...

"""
Added in 4.4.0
Source: https://developer.blender.org/docs/release_notes/4.4/animation_rigging/#slotted-actions
"""

# 1st phase of refactoring actions to be layered.
# Adds the action Slots feature, and Channel Bags, Layers, Strips to the API (not exposed in UI yet, so one-strip limit)
HAS_ANIM_LAYERED_1_STABLE = check_ver(4, 4, 0, 'alpha', tie_breaker_func=lambda: not _ANIM_LAYERED_1_EXPERIMENTAL)
if HAS_ANIM_LAYERED_1_STABLE:
    assert(not _ANIM_LAYERED_1_EXPERIMENTAL)

"""
Added in 4.5.0
Sources:
* https://developer.blender.org/docs/release_notes/4.5/rendering/#new-light-controls
* https://developer.blender.org/docs/release_notes/4.5/python_api/#pipeline-io
"""

HAS_LIGHT_TEMPERATURE = class_has_rna_prop(bpy.types.Light, 'temperature')
HAS_LIGHT_EXPOSURE = class_has_rna_prop(bpy.types.Light, 'exposure')
HAS_SMOOTH_GROUPS_BOUNDARY_VERTICES_PARAM = class_rna_func_has_param(bpy.types.Mesh, 'calc_smooth_groups',
                                                                     'use_boundary_vertices_for_bitflags')
