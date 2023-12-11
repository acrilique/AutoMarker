import bpy
import shutil, os
from addon_utils import enable
from automarker import basedir

src_dir = basedir + "/blender_command_port"
dst_dir = bpy.utils.script_path_user() + "/addons/blender_command_port"

print(src_dir)
print("hey")
# shutil.copytree(src_dir, dst_dir)

# addon = enable(module="blender_command_port", default_set=True, persistent=True, handle_error=None)
