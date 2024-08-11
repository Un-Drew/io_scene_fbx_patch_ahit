# Blender FBX - patched for A Hat in Time

This is a modification of the core FBX add-on that ships with Blender, that aims to fix several compatibility issues with the A Hat in Time modding tools (and possibly other Unreal Engine 3 games).

Changes include:
* Root bone fixes (import and export): No more missing/extra bones when porting skeletons!
* Animation batch-exporting: Each animation can be exported as an individual file.
* Scale animation fixes: Support for `Aligned` scale inheritance.

...and more™! You can find a **[full list of fixes & additions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Fixes-&-Additions)** on the wiki.

The source code of the vanilla add-on (the one that ships with Blender) can be found **[here](https://github.com/blender/blender/tree/main/scripts/addons_core/io_scene_fbx)**.

# Downloading and installing

This patch can be downloaded from the [Releases](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/releases) tab, and installed like any other Blender add-on. You can also find [detailed install instructions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Install-instructions) on the wiki.

> [!NOTE]
> Legacy versions are also available, hovever they don't function as a separate add-on, and thus have their own install instructions.

# Links

* [Releases](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/releases) - Downloads of the patch can be found here.
* [Install instructions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Install-instructions)
* [Full list of fixes & additions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Fixes-&-Additions)
* [Changelog](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Changelog)
* [Issues](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/issues) - Any issues you may find with the patch can be reported here.
* [Source code of the original add-on](https://github.com/blender/blender/tree/main/scripts/addons_core/io_scene_fbx)
