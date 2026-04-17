# Blender FBX - patched for A Hat in Time

This is a modified FBX add-on that aims to fix several compatibility issues with the A Hat in Time modding tools (and possibly other Unreal Engine 3 games).

Changes include:
* Root bone fixes (import and export): It no longer removes/adds a root bone from skeletons.
* Animation batch-exporting: Each animation can be exported as a separate `.fbx` file.
* Scale animation fixes: Support for more scale inheritance modes, like `Aligned`.

...and more! You can find a **[full list of fixes & additions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Fixes-&-Additions)** on the wiki.

# Downloading and installing

This patch can be downloaded from the [Releases](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/releases) tab, and installed like any other Blender add-on. You can also find [detailed install instructions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Install-instructions) on the wiki.

> [!NOTE]
> Legacy versions are also available, hovever they don't function as a separate add-on, and thus have their own install instructions.

# Links

* [Releases](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/releases) - Downloads of the patch can be found here.
* [Install instructions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Install-instructions)
* [Full list of fixes & additions](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Fixes-&-Additions)
* [Changelog](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/wiki/Changelog)
* [Issues and Requests](https://github.com/Un-Drew/io_scene_fbx_patch_ahit/issues) - Any issues you may find with the patch can be reported here. This can also be used to make feature requests.
* Add-on based on [io_scene_fbx_compat](https://github.com/Un-Drew/io_scene_fbx_compat) for backwards-compatibility.
