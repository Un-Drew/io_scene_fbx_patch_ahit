import shutil
import os.path
import subprocess
import colorama
import argparse
import sys

def make(addon_dir, output_zip_filename_without_ext):
    """
    Zips the scripts in `addon_dir` into a Blender addon/extension.
    The addon's .py files are expected to exist directly in the specified `addon_dir`, with no extra nesting.

    NOTE: The scripts in the generated .zip file will be placed in a directory, not at top-level. Even though
          Blender 4.2 extensions normally don't generate/need that nesting, it's required for addons in pre-4.2.

          Fortunately, newer Blenders are intentionally lenient with this. See pkg_zipfile_detect_subdir_or_none():
          https://projects.blender.org/blender/blender/src/tag/v5.0.0/scripts/addons_core/bl_pkg/cli/blender_ext.py#L845
    """
    shutil.make_archive(output_zip_filename_without_ext, 'zip',
            root_dir= os.path.join(addon_dir, ".."),
            base_dir=addon_dir)

def validate(blender_exe, zip_filename_without_ext):
    """
    Checks that the generated .zip is a valid post-4.2 extension.
    """
    completed_process = subprocess.run([blender_exe, "--command", "extension", "validate",
                                        zip_filename_without_ext + ".zip"])
    pref = (colorama.Fore.GREEN + "SUCCESS: ") if completed_process.returncode == 0 else (colorama.Fore.RED + "ERROR: ")
    print(pref + "Blender validation exited with", completed_process.returncode, colorama.Fore.RESET)
    return completed_process.returncode

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script to build io_scene_fbx_patch_ahit.zip, usable as both an"
                                                 " extension, and in the case of older Blenders, as a legacy addon")
    parser.add_argument("-b", "--blenderexe", help="Path to a Blender exe (>= v.4.2.0), used for validating the .toml."
                                                   " If unspecified, this will attempt to simply run 'blender'")
    args = parser.parse_args()
    output_filename = os.path.join("out", "io_scene_fbx_patch_ahit")
    make(addon_dir="io_scene_fbx_patch_ahit", output_zip_filename_without_ext=output_filename)
    returncode = 1
    try:
        returncode = validate(blender_exe=args.blenderexe if args.blenderexe else "blender",
                              zip_filename_without_ext=output_filename)
    except FileNotFoundError:
        if args.blenderexe:
            print(colorama.Fore.RED + "ERROR: No such executable file: '" + args.blenderexe + "'" + colorama.Fore.RESET)
        else:
            print(colorama.Fore.RED + "ERROR: Unable to execute 'blender'. Perhaps it's not in PATH?"
                    " Consider using the --blenderexe argument." + colorama.Fore.RESET)
    sys.exit(returncode)
