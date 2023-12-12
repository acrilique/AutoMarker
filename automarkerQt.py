# AutoMarker by acrilique.
# This script is a Qt version of the original automarker.py script by acrilique.
from PySide6.QtCore import QThread, Signal, Qt, QRect, QLineF, QPointF
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QSlider, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QGroupBox, QWidget
from PySide6.QtGui import QIcon, QPainter, QColor, QLinearGradient, QGradient
import librosa
import pyaudio
import requests
import os
import numpy
import sys
import re
import json
import subprocess
import platform
import time
import tempfile
from distutils.version import StrictVersion

###############################
###############################
###############################
# INITIAL SETUP
#  - Check what system are we in (Windows or macOS)
#  - Set the environment variables
#  - Set the basedir variable to the directory where the script is located
#  - Install premiere and blender extensions if needed
#  - Set the custom font
#  - Set the constants
#  Note: basedir isn't a constant because its location is decided at runtime
###############################

if platform.system().lower() == "windows":
    WINDOWS_SYSTEM = True
    import winreg as _winreg  # python 3
    RESOLVE_SCRIPT_API = "%PROGRAMDATA%\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting"
    RESOLVE_SCRIPT_LIB = "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll"
    PYTHONPATH = "%PYTHONPATH%;%RESOLVE_SCRIPT_API%\\Modules\\"
else:
    # if not windows, assume it is a macOS
    WINDOWS_SYSTEM = False
    RESOLVE_SCRIPT_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
    RESOLVE_SCRIPT_LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
    PYTHONPATH = "$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"

# Set the environment variables
os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_SCRIPT_API
os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_SCRIPT_LIB
os.environ["PYTHONPATH"] = PYTHONPATH

if getattr(sys, 'frozen', False):
   basedir = sys._MEIPASS
else:
   basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.

    myappid = "acrilique.automarker"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

try:
    flag_path = os.path.join(os.path.expanduser("~"), 'AutoMarker', 'flag.txt')
    with open(flag_path, 'r') as flag_file:
        flag_content = flag_file.read().strip()
except FileNotFoundError:
    # If the file is not found, treat it as not installed
    flag_content = "not_installed"

if flag_content == "not_installed":
    # Execute the batch script
    if WINDOWS_SYSTEM:
        subprocess.run([os.path.join(basedir, 'extension_installer_win.bat')])
    else:
        script_path = os.path.join(basedir, 'extension_installer_mac.sh')
        subprocess.run(['chmod', '+x', script_path])
        subprocess.run([script_path])
    os.makedirs(os.path.dirname(flag_path), exist_ok=True)
    # Update the flag.txt file to indicate that the script has been executed, erasing old text
    with open(flag_path, 'w') as flag_file:
        flag_file.write("installed")
        flag_file.close()

CREATE_NO_WINDOW = 0x08000000
PREMIERE_PROCESS_NAME = "adobe premiere pro.exe" if WINDOWS_SYSTEM else "Adobe Premiere Pro"
AFTERFX_PROCESS_NAME = "AfterFX.exe" if WINDOWS_SYSTEM else "After Effects"
RESOLVE_PROCESS_NAME = "Resolve.exe" if WINDOWS_SYSTEM else "Resolve"
BLENDER_PROCESS_NAME = "blender.exe" if WINDOWS_SYSTEM else "blender"
CEPPANEL_PROCESS_NAME = "CEPHtmlEngine.exe" if WINDOWS_SYSTEM else "CEPHtmlEngine"
SAMPLE_RATE = 44100

###########################################
###########################################
###########################################
# FUNCTIONS TO CHECK FOR RUNNING APPS AND LOOK PATHS TO EXECUTABLES
# - They are self-explanatory, and their purpose is to create an easy and multiplatform access to this functionality.
###########################################
def is_premiere_running():
    """
    Is there a running instance of the Premiere Pro app on this machine ?

    :return: (bool) process is running, (int) pid
    """
    return exe_is_running(PREMIERE_PROCESS_NAME)

def is_afterfx_running():

    return exe_is_running(AFTERFX_PROCESS_NAME)

def is_resolve_running():

    return exe_is_running(RESOLVE_PROCESS_NAME)

def start_premiere(use_bat=False):
    raise SystemError("Could not guaranty premiere started")

def start_afterfx(use_bat=False):
    raise SystemError("Could not guaranty afterfx started")

def exe_is_running(exe_name):
    """
    List processes by name to know if one is running

    :param exe_name: (str) exact name of the process (ex : 'pycharm64.exe' for windows or 'Safari' for mac)
    :return: (bool) process is running, (int) pid
    """
    pids = _get_pids_from_name(exe_name)
    if len(pids) == 1:
        return True, pids[0]
    if len(pids) > 1 and (exe_name == AFTERFX_PROCESS_NAME or exe_name == PREMIERE_PROCESS_NAME):
        return True, pids[0]
    if len(pids) > 1:
        raise OSError("More than one process matching name '{}' were found running (pid: {})".format(exe_name, pids))
    return False, None

def count_running_exe(exe_name):
    """
    List processes by name to know how many are running

    :param exe_name: (str) exact name of the process (ex : 'pycharm64.exe' for windows or 'Safari' for mac)
    :return: (int) Number of process with given name running
    """
    return len(_get_pids_from_name(exe_name))

def _get_pids_from_name(process_name):
    """
    Given a process name get ids of running process matching this name

    :param process_name: (str) process name (ex : 'pycharm64.exe' for windows or 'Safari' for mac)
    :return: (list of int) pids
    """
    if WINDOWS_SYSTEM:
        # use tasklist windows command with filter by name
        call = 'TASKLIST', '/FI', 'imagename eq {}'.format(process_name)
        output = subprocess.check_output(call, creationflags=CREATE_NO_WINDOW)
        if sys.version_info >= (3, 0):
            output = output.decode(encoding="437")  # encoding for windows console
        # parse output lines
        lines = output.strip().splitlines()
        matching_lines = [l for l in lines if l.lower().startswith(process_name.lower())]

        # print(f"Matching lines for {process_name}: {matching_lines}")

        return [int(re.findall("   ([0-9]{1,6}) [a-zA-Z]", l)[0]) for l in matching_lines]
    else:
        # use pgrep UNIX command to filter processes by name
        try:
            output = subprocess.check_output(["pgrep", process_name])
        except subprocess.CalledProcessError:  # pgrep seems to crash if the given name is not a running process...
            return list()
        # parse output lines
        lines = output.strip().splitlines()
        # print(f"Lines for {process_name}: {lines}")

        return list(map(int, lines))

def _get_last_exe_mac(app_name):
    """
    MACOS ONLY
    Get the executable path on disk of the last installed application version using macOS System Profiler

    :param app_name: (str) name of the application
    :return: (str) path to executable
    """
    # list all installed app to a json datastructure
    output = subprocess.check_output(["system_profiler", "-json", "SPApplicationsDataType"])
    apps_data = json.loads(output)["SPApplicationsDataType"]
    # filter installed versions of the specified application
    app_apps = [data for data in apps_data if app_name.lower() in data["_name"].lower()]
    if not app_apps:
        raise OSError(f"Could not find a {app_name} version installed on this computer")
    # get last app version path
    app_apps.sort(key=lambda d: d["version"], reverse=True)
    return app_apps[0]["path"]

def _get_last_exe_windows(app_name):
    """
    WINDOWS ONLY
    Get the executable path on disk of the last installed application version using windows registry

    :param app_name: (str) name of the application
    :return: (str) path to executable
    """
    app_versions = _get_installed_softwares_info(app_name.lower())
    if not app_versions:
        raise OSError(f"Could not find a {app_name} version installed on this computer")
    # find last installed version
    last_version_num = sorted([StrictVersion(v["DisplayVersion"]) for v in app_versions])[-1]
    last_version_info = [v for v in app_versions if v["DisplayVersion"] == str(last_version_num)][0]
    # search actual exe path
    base_path = last_version_info["InstallLocation"]
    build_year = last_version_info["DisplayName"].split(" ")[-1]
    wrong_paths = list()
    for folder_name in [f"{app_name} CC {{}}", f"{app_name} {{}}", ""]:  # different versions formatting
        exe_path = os.path.join(base_path, folder_name.format(build_year), f"{app_name}.exe")
        if not os.path.isfile(exe_path):
            wrong_paths.append(exe_path)
            continue
        wrong_paths = list()
        break
    if len(wrong_paths) != 0:
        raise IOError(f"Could not find {app_name} executable in '{wrong_paths}'")
    return exe_path

def _get_installed_softwares_info(name_filter, names=["DisplayVersion", "InstallLocation"]):
    """
    WINDOWS ONLY
    Looking into Uninstall key in Windows registry, we can get some infos about installed software

    :param name_filter: (str) filter software containing this name
    :return: (list of dict) info of software found
    """
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    key = _winreg.OpenKey(reg, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    apps_info = list()
    # list all installed apps
    for i in range(_winreg.QueryInfoKey(key)[0]):
        subkey_name = _winreg.EnumKey(key,i)
        subkey = _winreg.OpenKey(key, subkey_name)
        try:
            soft_name = _winreg.QueryValueEx(subkey, "DisplayName")[0]
        except EnvironmentError:
            continue
        if name_filter.lower() not in soft_name.lower():
            continue
        apps_info.append(dict({n: _winreg.QueryValueEx(subkey, n)[0] for n in names}, DisplayName=soft_name))
    return apps_info
###########################################
###########################################
###########################################
# INTERFACES TO HANDLE THE COMMUNICATION WITH THE APPS
###########################################
# AE interface
class AE_JSWrapper(object):
    def __init__(self, aeVersion = "", returnFolder = ""):
        self.aeVersion = aeVersion

        # Try to find last AE version if value is not specified. Currently 24.0 is the last version.
        if not len(self.aeVersion):
            if WINDOWS_SYSTEM:
                self.aeVersion = str(int(time.strftime("%Y")[2:]) + 1) + ".0" # 24.0
            else:# 2024
                self.aeVersion = str(int(time.strftime("%Y")) + 1) # 2024

        if WINDOWS_SYSTEM:
            # Get the AE_ exe path from the registry. 
            try:
                self.aeKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Adobe\\After Effects\\" + self.aeVersion)
            except:
                print ("ERROR: Unable to find After Effects version " + self.aeVersion + " on this computer\nTo get correct version number please check https://en.wikipedia.org/wiki/Adobe_After_Effects\nFor example, \"After Effect CC 2019\" is version \"16.0\"")

            self.aeApp = _winreg.QueryValueEx(self.aeKey, 'InstallPath')[0] + 'AfterFX.exe'          
        else:
            guess_path = "/Applications/Adobe After Effects " + self.aeVersion + "/Adobe After Effects " + self.aeVersion + ".app/Contents/aerendercore.app/Contents/MacOS/aerendercore"
            if os.path.exists(guess_path):
                self.aeApp = guess_path
            else:
                print ("ERROR: Unable to find After Effects version " + self.aeVersion + " on this computer\nTo get correct version number please check https://en.wikipedia.org/wiki/Adobe_After_Effects\nFor example, \"After Effect CC 2019\" is version \"16.0\"")
        ## WE SHOULD TRY THIS IN A MAC ENVIRONMENT.
        # if WINDOWS_SYSTEM:
        #     # Get the AE_ exe.
        #     try:
        #         self.aeApp = _get_last_exe_windows(AFTERFX_PROCESS_NAME)
        #     except Exception as e:
        #         print (e)
        #         pass
        # else:
        #     try:
        #         self.aeApp = _get_last_exe_mac(AFTERFX_PROCESS_NAME)
        #     except Exception as e:
        #         print (e)
        #         pass
        # Get the path to the return file. Create it if it doesn't exist.
        if not len(returnFolder):
            if WINDOWS_SYSTEM:
                returnFolder = os.path.join(tempfile.gettempdir(), "AutoMarker")
            else:
                returnFolder = os.path.join(os.path.expanduser("~"), "Documents", "AutoMarker")
        self.returnFile = os.path.join(returnFolder, "ae_temp_ret.txt")
        if not os.path.exists(returnFolder):
            os.mkdir(returnFolder)
        
        # Ensure the return file exists...
        with open(self.returnFile, 'w') as f:
                f.close()  
            
        # Establish the last time the temp file was modified. We use this to listen for changes. 
        self.lastModTime = os.path.getmtime(self.returnFile)         
        
        # Temp file to store the .jsx commands. 
        self.tempJsxFile = os.path.join(returnFolder, "ae_temp_com.jsx")
        
        # This list is used to hold all the strings which eventually become our .jsx file. 
        self.commands = []    

    def openAE(self):
        """Pass the commands to the subprocess module."""    
        target = [self.aeApp]
        ret = subprocess.Popen(target)
    
    # This group of helper functions are used to build and execute a jsx file.
    def jsNewCommandGroup(self):
        """clean the commands list. Called before making a new list of commands"""
        self.commands = []

    def jsExecuteCommand(self):
        if WINDOWS_SYSTEM:
            target = [self.aeApp, "-ro", self.tempJsxFile]
        else:
            # Get the absolute path to the JSX file
            jsx_file_path = os.path.abspath(self.tempJsxFile)
            
            # Activate After Effects
            subprocess.Popen(['osascript', '-e', f'tell application "Adobe After Effects {self.aeVersion}" to activate'])
            time.sleep(0.1)  # Wait for After Effects to activate
            
            # Run the JSX script
            target = ['osascript', '-e', f'tell application "Adobe After Effects {self.aeVersion}" to DoScriptFile "{jsx_file_path}"']
        ret = subprocess.Popen(target)

    def jsWriteDataOut(self, returnRequest):
        """ An example of getting a return value"""
        com = (
            """
            var retVal = %s; // Ask for some kind of info about something. 
            
            // Write to temp file. 
            var datFile = new File("[DATAFILEPATH]"); 
            datFile.open("w"); 
            datFile.writeln(String(retVal)); // return the data cast as a string.  
            datFile.close();
            """ % (returnRequest)
        )

        returnFileClean = "/" + self.returnFile.replace("\\", "/").replace(":", "").lower()
        com = com.replace("[DATAFILEPATH]", returnFileClean)

        self.commands.append(com)        
        
    def readReturn(self):
        """Helper function to wait for AE to write some output for us."""
        # Give time for AE to close the file...
        time.sleep(0.1)        
        
        self._updated = False
        while not self._updated:
            self.thisModTime = os.path.getmtime(self.returnFile)
            if str(self.thisModTime) != str(self.lastModTime):
                self.lastModTime = self.thisModTime
                self._updated = True
        
        f = open(self.returnFile, "r+")
        content = f.readlines()
        f.close()

        res = []
        for item in content:
            res.append(str(item.rstrip()))
        return res
class AE_JSInterface(object):
    
    def __init__(self, aeVersion = "", returnFolder = ""):
        self.aeWindowName = "Adobe After Effects"
        self.aeCom = AE_JSWrapper(aeVersion, returnFolder) # Create wrapper to handle JSX

    def openAE(self):
        self.aeCom.openAE()

    def addMarkers(self, list):
        jsxTodo = f"""

        var item = app.project.activeItem;
        var beats = {list};
        if (app.project.activeItem instanceof CompItem) {{

            var comp = app.project.activeItem;
        }} else if (app.project.item(1) instanceof CompItem) {{
            var comp = app.project.item(1);
        }}

        for (var i = 0; i < beats.length;  i++) {{
            var compMarker = new MarkerValue(String(i));
            comp.markerProperty.setValueAtTime(beats[i], compMarker);
        }}             

        """
        with open(self.aeCom.tempJsxFile, 'w') as f:
            f.write(jsxTodo)
            f.close()

        self.aeCom.jsExecuteCommand()
        time.sleep(0.1)
    
    def clearAllMarkers(self):
        jsxTodo = f"""

        var item = app.project.activeItem;

        if (app.project.activeItem instanceof CompItem) {{
            var comp = app.project.activeItem;
        }} else if (app.project.item(1) instanceof CompItem) {{
            var comp = app.project.item(1);
        }}
        $
        for (var i = comp.markerProperty.numKeys; i > 0; i = i - 1) {{
            comp.markerProperty.removeKey(1);
        }}
        """
        with open(self.aeCom.tempJsxFile, 'w') as f:
            f.write(jsxTodo)
            f.close()

        self.aeCom.jsExecuteCommand()
        time.sleep(0.1)
###########################################
###########################################
# Premiere interface
class PR_JSWrapper(object):
    def __init__(self, prVersion = "", returnFolder = ""):
        self.jsxTodo = ""
    
    def jsExecuteCommand(self):
        json_data = json.dumps({"to_eval": self.jsxTodo})
        response = requests.post("http://127.0.0.1:3000", data=json_data)
# Actual interface
class PR_JSInterface(object):

    def __init__(self, prVersion = "", returnFolder = ""):

        self.prCom = PR_JSWrapper(prVersion, returnFolder) # Create wrapper to handle JSX

    def addMarkers(self, list):
        self.prCom.jsxTodo = f"""

        for (var i = 0; i < {list}.length;  i++) {{
            $.writeln("list[i]: " + {list}[i]);
            $.writeln("end: " + app.project.activeSequence.end);
            if ({list}[i] < app.project.activeSequence.end)
            app.project.activeSequence.markers.createMarker({list}[i]);
        }}             

        """

        self.prCom.jsExecuteCommand()
        time.sleep(0.1)

    def clearAllMarkers(self):
        self.prCom.jsxTodo = f"""

        var markers = app.project.activeSequence.markers;
        var current_marker = markers.getFirstMarker();
        while (markers.numMarkers > 0) {{
            var to_delete = current_marker;
            current_marker = markers.getNextMarker(current_marker);
            markers.deleteMarker(to_delete);
        }}

        """
        self.prCom.jsExecuteCommand()
        time.sleep(0.1)
###########################################
###########################################
# Resolve interface
class Resolve_Interface(object):

    def __init__(self):
        self.resolve = Resolve_Interface.GetResolve()

    def GetResolve():
        try:
        # The PYTHONPATH needs to be set correctly for this import statement to work.
        # An alternative is to import the DaVinciResolveScript by specifying absolute path (see ExceptionHandler logic)
            import DaVinciResolveScript as bmd
        except ImportError:
            if sys.platform.startswith("darwin"):
                expectedPath="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
            elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
                import os
                expectedPath=os.getenv('PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
            elif sys.platform.startswith("linux"):
                expectedPath="/opt/resolve/libs/Fusion/Modules/"

            # check if the default path has it...
            print("Unable to find module DaVinciResolveScript from $PYTHONPATH - trying default locations")
            try:
                import imp
                bmd = imp.load_source('DaVinciResolveScript', expectedPath+"DaVinciResolveScript.py")
            except ImportError:
                # No fallbacks ... report error:
                print("Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
                print("For a default DaVinci Resolve installation, the module is expected to be located in: "+expectedPath)
                sys.exit()

        return bmd.scriptapp("Resolve")
    
    def addMarkers(self, list, color = "Blue"):
        resolve = self.resolve
        if not resolve:
            print("Error: Failed to get resolve object!")
            return

        # Get supporting objects
        projectManager = resolve.GetProjectManager()
        project = projectManager.GetCurrentProject()
        timeline = project.GetCurrentTimeline()  # current timeline

        if not timeline:
            print("Error: No current timeline exist, add a timeline (recommended duration >= 80 frames) and try again!")
            return

        # Open Edit page
        resolve.OpenPage("edit")

        # Get timeline frames
        startFrame = int(timeline.GetStartFrame())
        endFrame = int(timeline.GetEndFrame())
        numFrames = endFrame - startFrame
        framerate = timeline.GetSetting("timelineFrameRate")

        # Add Markers
        for beat in list:
            frame = int(beat * framerate)
            if numFrames >= 1:
                try: timeline.DeleteMarkerAtFrame(frame)
                except: pass
                isSuccess = timeline.AddMarker(frame, "Blue", "AutoMarker", "beat-related", 1)

    def clearAllMarkers(self):
        resolve = self.resolve
        if not resolve:
            print("Error: Failed to get resolve object!")
            return

        # Get supporting objects
        projectManager = resolve.GetProjectManager()
        project = projectManager.GetCurrentProject()
        timeline = project.GetCurrentTimeline()  # current timeline

        if not timeline:
            print("Error: No current timeline exist, add a timeline (recommended duration >= 80 frames) and try again!")
            return

        # Open Edit page
        resolve.OpenPage("edit")
        timeline.DeleteMarkersByColor("Blue")
###############################
###############################
###############################
# QT CLASSES
class Layout(QWidget):
    # this class is only for the set of widgets that are inside the main window, not menubar or statusbar
    def __init__(self):
        super().__init__()
        self.create_markers_button = QPushButton("Create markers")
        self.create_markers_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.create_markers_button.setMaximumHeight(150)
        self.remove_markers_button = QPushButton("Remove markers")
        
        self.group_box = QGroupBox("")       
        self.group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) 
        self.every_slider = QSlider(Qt.Horizontal)
        self.every_slider.setRange(1, 16)
        self.every_slider.setValue(4)
        self.every_slider.setTickInterval(1)

        self.offset_slider = QSlider(Qt.Horizontal)
        self.offset_slider.setRange(0, 16)
        self.offset_slider.setValue(0)
        self.offset_slider.setTickInterval(1)

        self.group_box_layout = QVBoxLayout()
        self.every_label = QLabel("Place markers every x beats")
        self.group_box_layout.addWidget(self.every_label)
        self.group_box_layout.addWidget(self.every_slider)

        self.offset_label = QLabel("Offset first beat")
        self.group_box_layout.addWidget(self.offset_label)
        self.group_box_layout.addWidget(self.offset_slider)

        self.group_box.setLayout(self.group_box_layout)

        self.left_v_layout = QVBoxLayout()
        self.left_v_layout.addWidget(self.create_markers_button, 2)
        self.left_v_layout.addWidget(self.remove_markers_button, 1)
        self.left_v_layout.addWidget(self.group_box, 1)

        self.h_layout = QHBoxLayout()
        self.h_layout.addLayout(self.left_v_layout, 1)

        self.setLayout(self.h_layout)
    
    def add_preview(self, analyzer_data, beats, sample_rate):
        self.data = analyzer_data.tolist()
        self.beats = beats.tolist()
        self.sample_rate = sample_rate

        self.waveform_display = WaveformDisplay()

        self.right_v_layout = QVBoxLayout()
        self.right_v_layout.addWidget(self.waveform_display)
        self.h_layout.addLayout(self.right_v_layout, 3)

        self.global_offset_label = QLabel("Global offset")
        self.left_global_offset_button = QPushButton("<<")
        self.right_global_offset_button = QPushButton(">>")
        self.global_offset_buttons_layout = QHBoxLayout()
        self.global_offset_buttons_layout.addWidget(self.global_offset_label)
        self.global_offset_buttons_layout.addWidget(self.left_global_offset_button)
        self.global_offset_buttons_layout.addWidget(self.right_global_offset_button)
        self.group_box_layout.addLayout(self.global_offset_buttons_layout)

        self.zoom_box = QGroupBox("")
        self.zoom_box_layout = QVBoxLayout()
        self.zoom_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) 
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(80, 99)
        self.zoom_slider.setValue(99)
        self.zoom_slider.setTickInterval(1)
        self.zoom_box_layout.addWidget(QLabel("Zoom"))
        self.zoom_box_layout.addWidget(self.zoom_slider)

        self.scroll_slider = QSlider(Qt.Horizontal)
        self.scroll_slider.setRange(0, len(self.data))
        self.scroll_slider.setValue(0)
        self.scroll_slider.setTickInterval(1)
        self.zoom_box_layout.addWidget(QLabel("Scroll"))
        self.zoom_box_layout.addWidget(self.scroll_slider)

        self.zoom_box.setLayout(self.zoom_box_layout)
        self.left_v_layout.addWidget(self.zoom_box)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_v_layout.addWidget(self.play_pause_button)

        self.update_chart()
        self.zoom_slider.valueChanged.connect(self.update_chart)
        self.scroll_slider.valueChanged.connect(self.update_chart)
        self.offset_slider.valueChanged.connect(self.update_chart)
        self.every_slider.valueChanged.connect(self.update_chart)
        self.waveform_display.zoom_signal.connect(self.handle_zoom_signal)
        self.waveform_display.scroll_signal.connect(self.handle_scroll_signal)

    def handle_zoom_signal(self, delta):
        if int(delta) > 0:
            self.zoom_slider.setValue(self.zoom_slider.value() + 1)
        else:
            self.zoom_slider.setValue(self.zoom_slider.value() - 1)
        self.update_chart()

    def handle_scroll_signal(self, delta):
        if int(delta) > 0:
            self.scroll_slider.setValue(self.scroll_slider.value() + 1)
        else:
            self.scroll_slider.setValue(self.scroll_slider.value() - 1)
        self.update_chart()

    def update_chart(self):
        zoom = self.zoom_slider.value() / 100
        scroll = self.scroll_slider.value() / len(self.data)
        offset = self.offset_slider.value()
        every = self.every_slider.value()

        visible_data_length = int(len(self.data) * (1 - zoom))
        start = int((len(self.data) - visible_data_length) * scroll)
        end = start + visible_data_length

        beats_in_samples = [beat * self.sample_rate for beat in self.beats]
        visible_beats = [beat - start for beat in beats_in_samples if start <= beat < end]
        selected_beats = visible_beats[offset::every]

        self.waveform_display.set_samples(self.data[start:end], selected_beats)

class WaveformDisplay(QWidget):
    """Custom widget for waveform representation of a digital audio signal."""
    zoom_signal = Signal(int)
    scroll_signal = Signal(int)
    def __init__(self, frames=None, channels=1, samplerate=SAMPLE_RATE, beats=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sampleframes = frames
        self._beatsamples = beats
        self._channels = channels
        self._samplerate = samplerate
        self.waveform_color = QColor('#B0B1B5') 
        # ~ self.waveform_color = QtGui.QColor(255, 255, 255, 160)
        self.background_color = QColor('#838487')
        self.background_gradient = QLinearGradient()
        self.background_gradient.setColorAt(0, QColor('black'))
        self.background_gradient.setColorAt(1, QColor('#838487'))
        self.background_gradient.setSpread(QGradient.Spread.ReflectSpread)
        self.foreground_color = QColor('white')
        self._zoom = 1.0
        self._startframe = 0
        self._endframe = -1
        self.play_position = 0

    def wheelEvent(self, event):
        deltay = event.angleDelta().y()
        deltax = event.angleDelta().x()
        if deltay != 0:
            self.zoom_signal.emit(deltay)
        if deltax != 0:
            self.scroll_signal.emit(deltax)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        self.draw_waveform(painter)
        self.draw_markers(painter)
        self.draw_track_line(painter)
        painter.end()

    def draw_track_line(self, painter):
        pen = painter.pen()
        pen.setColor(QColor('#ED37A4'))  # Set the color for the track line
        pen.setWidth(2)
        painter.setPen(pen)

        width = painter.device().width()
        x = self.play_position * width / len(self._sampleframes)
        painter.drawLine(QPointF(x, 0), QPointF(x, painter.device().height()))

    def update_play_position(self, play_position):
        self.play_position = play_position
        self.update()

    def draw_markers(self, painter):
        pen = painter.pen()
        pen.setColor(QColor('#254E5C'))  # Set the color for the markers
        pen.setWidth(3)
        painter.setPen(pen)

        width = painter.device().width()
        visible_samples = len(self._sampleframes[self._startframe:self._endframe])

        for beat in self._beatsamples:
            # Subtract the start frame index from the beat sample index
            beat -= self._startframe
            x = beat * width / visible_samples
            painter.drawLine(QPointF(x, 0), QPointF(x, painter.device().height()))

    def draw_waveform(self, painter):
        pen = painter.pen()
        pen.setColor("#88BDA6")  
        height = painter.device().height()
        zero_y = float(height) / 2
        width = painter.device().width()
        num_frames = len(self._sampleframes[self._startframe:self._endframe])
        samples_per_pixel = num_frames / float(width)

        # draw background
        # ~ brush = QtGui.QBrush()
        # ~ brush.setColor(self.background_color)
        # ~ brush.setStyle(Qt.BrushStyle.SolidPattern)
        self.background_gradient.setStart(0.0, zero_y)
        self.background_gradient.setFinalStop(0.0, 0.0)
        rect = QRect(0, 0, width, height)
        painter.fillRect(rect, self.background_gradient)
        startframe = self._startframe

        # draw waveform
        if self._sampleframes is not None:
            pen.setColor(self.waveform_color)
            painter.setPen(pen)
            for pixel in range(width):
                offset = round(pixel * samples_per_pixel)

                if 0 <= offset < num_frames:
                    start = startframe + offset
                    end = max(start + 1, start + int(samples_per_pixel))
                    values = self._sampleframes[start:end]
                    max_value = max(values)
                    min_value = min(values)

                    if max_value > 0:
                        y = zero_y - zero_y * max_value
                        painter.drawLine(QLineF(pixel, zero_y, pixel, y))
                    if min_value < 0:
                        y = zero_y - zero_y * min_value
                        painter.drawLine(QLineF(pixel, zero_y, pixel, y))

        # draw zero line
        pen.setColor(self.foreground_color)
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.drawLine(QLineF(0.0, zero_y, float(width), zero_y))

    def set_samples(self, frames, beats, channels=1, samplerate=SAMPLE_RATE):
        self._sampleframes = frames if frames is not None else []
        self._beatsamples = beats
        self._channels = channels
        self._samplerate = samplerate
        self.update()

class StatusChecker(QThread):
    statusChanged = Signal(str)

    def run(self):
        while True:
            if is_premiere_running()[0]:
                self.statusChanged.emit("1")
            elif is_afterfx_running()[0]:
                self.statusChanged.emit("2")
            elif is_resolve_running()[0]:
                self.statusChanged.emit("3")
            else:
                self.statusChanged.emit("0")
            time.sleep(1)
class AddMarkersThread(QThread):

    finished = Signal()

    def __init__(self, app, beatsamples, every=1, offset=0):
        super().__init__()
        self.app = app
        self.beatsamples = beatsamples
        self.every = every
        self.offset = offset

    def run(self):
        if self.app is not None:
            markers = self.beatsamples.tolist()[self.offset::self.every]
            self.app.addMarkers(markers)

class RemoveMarkersThread(QThread):

    finished = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):
        if self.app is not None:
            self.app.clearAllMarkers()
class Analyzer(QThread):

    finished = Signal()

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        self.data, self.samplerate = librosa.load(path=self.path, sr=SAMPLE_RATE, mono=True)
        self.tempo, self.beatsamples = librosa.beat.beat_track(y=self.data, units="time", sr=SAMPLE_RATE)
class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("AutoMarker")
        self.setWindowIcon(QIcon(os.path.join(basedir, "icon.png")))
        self.resize(260, 240)
        self.setStyleSheet("""
                           QMainWindow {
                                background-color: #838487;
                           } 
                           QGroupBox { 
                                border: 1px solid gray; 
                                border-radius: 7px;
                           }
                           """)
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        help_menu = menu_bar.addMenu("Help")

        select_file_action = file_menu.addAction("Select audio file")
        select_file_action.triggered.connect(self.select_file)

        readme_action = help_menu.addAction("Readme")
        readme_action.triggered.connect(lambda: os.startfile(os.path.join(basedir, 'README.md')))

        status_bar = self.statusBar()
        status_bar.showMessage("Ready")
        self.app_status_label = QLabel("")
        status_bar.addPermanentWidget(self.app_status_label)

        self.status_checker = StatusChecker()
        self.status_checker.statusChanged.connect(self.update_app_status)
        self.status_checker.start()

        self.widget_layout = Layout()
        self.widget_layout.layout()
        self.setCentralWidget(self.widget_layout)
        # Connect the signals
        self.widget_layout.create_markers_button.clicked.connect(self.add_markers)
        self.widget_layout.remove_markers_button.clicked.connect(self.remove_markers)

    def negative_global_offset(self):
        # reduces all beat values (which are in seconds) by 0.1
        self.analyzer.beatsamples -= 0.01
        self.widget_layout.beats = self.analyzer.beatsamples.tolist()
        self.widget_layout.update_chart()
    
    def positive_global_offset(self):
        # increases all beat values (which are in seconds) by 0.1
        self.analyzer.beatsamples += 0.01
        self.widget_layout.beats = self.analyzer.beatsamples.tolist()
        self.widget_layout.update_chart()

    def add_markers(self):
        self.statusBar().showMessage("Placing markers...")
        self.add_markers_thread = AddMarkersThread(self.current_app, self.analyzer.beatsamples, self.widget_layout.every_slider.value(), self.widget_layout.offset_slider.value())
        self.add_markers_thread.start()
        self.add_markers_thread.finished.connect(lambda: self.statusBar().showMessage("Done!"))

    def remove_markers(self):
        self.statusBar().showMessage("Removing markers...")
        self.remove_markers_thread = RemoveMarkersThread(self.current_app)
        self.remove_markers_thread.start()
        self.remove_markers_thread.finished.connect(lambda: self.statusBar().showMessage("Done!"))

    def update_app_status(self, status):
        if (status == "0"):
            self.app_status_label.setText("App isn't running...")
            self.current_app = None
        elif (status == "1"):
            self.current_app = PR_JSInterface()
            self.app_status_label.setText("Premiere Pro is running!")
        elif (status == "2"):
            self.current_app = AE_JSInterface()
            self.app_status_label.setText("After Effects is running!")
        elif (status == "3"):
            self.current_app = Resolve_Interface()
            self.app_status_label.setText("Resolve is running!")

    def select_file(self):
        self.statusBar().showMessage("Selecting file...")
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an audio file", os.path.expanduser("~"), "Audio files (*.wav *.mp3 *.flac *.ogg *.aiff);;All files (*.*)")
        if file_path:
            self.path = file_path
            self.retreive_and_preview()
        else:
            self.statusBar().showMessage("No file was selected! Try again.")

    def retreive_and_preview(self):
        self.statusBar().showMessage("Reading file from source...")
        self.analyzer = Analyzer(self.path)
        self.analyzer.finished.connect(self.preview)
        self.analyzer.start()
    
    def preview(self):
        self.resize(1000, 500)
        self.statusBar().showMessage("Displaying preview...")
        self.widget_layout.add_preview(self.analyzer.data, self.analyzer.beatsamples, self.analyzer.samplerate)
        self.widget_layout.play_pause_button.clicked.connect(self.start_stop_playback)
        self.widget_layout.left_global_offset_button.clicked.connect(self.negative_global_offset)
        self.widget_layout.right_global_offset_button.clicked.connect(self.positive_global_offset)

    def start_stop_playback(self):
        if self.widget_layout is not None:
            self.data = self.analyzer.data
            if self.widget_layout.play_pause_button.text() == "Play":
                
                self.widget_layout.play_pause_button.setText("Pause")
                self.start_audio_playback()
            else:
                self.widget_layout.play_pause_button.setText("Play")
                self.stop_audio_playback()

    def start_audio_playback(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=self.analyzer.samplerate,
                                  output=True,
                                  stream_callback=self.callback)
        self.stream.start_stream()

    def stop_audio_playback(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, status):
        data = self.data[:frame_count]
        self.data = self.data[frame_count:]
        
        # Calculate the current play position based on the number of frames that have been played
        current_play_position = len(self.analyzer.data) - len(self.data)
        
        # Get the current zoom and scroll values
        zoom = self.widget_layout.zoom_slider.value() / 100
        scroll = self.widget_layout.scroll_slider.value() / len(self.data)
        
        # Adjust the play position based on the zoom and scroll values
        visible_data_length = int(len(self.data) * (1 - zoom))
        start = int((len(self.data) - visible_data_length) * scroll)
        adjusted_play_position = current_play_position - start
        
        # Update the play position of the waveform_display widget
        self.widget_layout.waveform_display.update_play_position(adjusted_play_position)
        
        return (data.tobytes(), pyaudio.paContinue)
        
app = QApplication(sys.argv)
window = MainWindow(app)
window.show()
app.exec()