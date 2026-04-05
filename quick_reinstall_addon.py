import sys
import pathlib
import os
import colorama
import shutil

def get_blender_user_dir():
    """
    Function that attempts to get the Blender user directory depending on the current OS.
    """
    platform = sys.platform
    user_home_dir = pathlib.Path.home()
    match platform:
        case "win32":
            return os.path.join(user_home_dir, "AppData", "Roaming", "Blender Foundation", "Blender")
        case "linux" | "linux2":
            if "XDG_CONFIG_HOME" in os.environ:
                return os.path.join(os.environ["XDG_CONFIG_HOME"], "blender")  # XXX: NOT TESTED!
            else:
                return os.path.join(user_home_dir, ".config", "blender")
        case "darwin":  # i.e. OS X
            return os.path.join(user_home_dir, "Library", "Application Support", "Blender")  # XXX: NOT TESTED!
        case _:
            print(colorama.Fore.RED + "Can't determine Blender user directory for platform:", platform, colorama.Fore.RESET)
            sys.exit(1)

def copy_addon_to(addon_src_dir, addon_dst_dir):
    # XXX: This adds new files, overwrites modified files, but doesn't remove deleted files.
    shutil.copytree(addon_src_dir, addon_dst_dir, dirs_exist_ok=True)

def reinstall(addon_dir_to_reinstall, addon_name):
    """
    Utility for quick-reinstalling a blender addon's files, to avoid tedious menu-ing after incremental changes.
    `addon_dir_to_reinstall` must point to the dir that directly contains the py scripts.
    `addon_name` must be the name of the addon. Likely same name as `addon_dir_to_reinstall`.
    """
    blender_user_dir = get_blender_user_dir()
    if not os.path.isdir(blender_user_dir):
        print(colorama.Fore.RED + "Directory", blender_user_dir, "doesn't exist!")
        sys.exit(1)
    blender_ver_folders = os.listdir(blender_user_dir)
    blender_ver_folders.sort()  # Sort them because it looks nicer when logged.
    for blender_ver_name in blender_ver_folders:
        version_specific_dir = os.path.join(blender_user_dir, blender_ver_name)
        if not os.path.isdir(version_specific_dir):
            continue
        addon_dst_dir = ...
        if os.path.isdir(os.path.join(version_specific_dir, "extensions", "user_default")):
            addon_dst_dir = os.path.join(version_specific_dir, "extensions", "user_default", addon_name)
        elif os.path.isdir(os.path.join(version_specific_dir, "scripts", "addons")):
            addon_dst_dir = os.path.join(version_specific_dir, "scripts", "addons", addon_name)
        else:
            continue
        if not os.path.isdir(addon_dst_dir):
            continue
        copy_addon_to(addon_dir_to_reinstall, addon_dst_dir)
        print(colorama.Fore.GREEN + "Updated addon for ver", blender_ver_name, colorama.Fore.RESET)

if __name__ == '__main__':
    reinstall(addon_dir_to_reinstall="io_scene_fbx_patch_ahit", addon_name="io_scene_fbx_patch_ahit")
