# Blender FBX - patched for A Hat in Time

**NOTE: This project is a work-in-progress! Things are subject to change. A lot.**

This is a modification of the core FBX add-on that ships with Blender, that aims to fix several compatibility issues with the A Hat in Time modding tools (and possibly other Unreal Engine 3 games).

Changes include:
* Root bone fixes (import and export): No more missing/extra bones when porting skeletons!
* Animation batch-exporting: Each animation can be exported as an individual file.
* Scale animation fixes: Support for `Aligned` scale inheritance.

...and more™! You can find a **[full list of fixes & additions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Fixes-&-Additions)** on the wiki.

The source code of the vanilla add-on (the one that ships with Blender) can be found **[here](https://github.com/blender/blender/tree/main/scripts/addons_core/io_scene_fbx)**.
