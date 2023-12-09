# AutoMarker by acrilique.
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from threading import Thread
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

###############################
###############################
###############################
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

###############################
###############################
###############################
###############################

def update_runvar():

    global aeApp, prApp
    if(is_premiere_running()[0]):
        if (prApp==None):
            prApp = PR_JSInterface()
        runvar.set("Premiere Pro is running!")
    elif(is_afterfx_running()[0]):
        if (aeApp==None):
            aeApp = AE_JSInterface()
        runvar.set("After Effects is running!")
    elif(is_resolve_running()[0]):
        runvar.set("Resolve is running!")
    else:
        runvar.set("App isn't running...")
    root.after(1000, update_runvar)

def auto_beat_marker():
    if (is_premiere_running()[0] or is_afterfx_running()[0] or is_resolve_running()[0]):
        thread = Thread(target=place_marks)
        thread.daemon = True
        thread.start()

def place_marks():
    global data

    every = everyvar.get()
    offset = offsetvar.get()
    beatsamplestoplace = beatsamples[offset::every]
    
    info.set("Placing markers...")
    root.update()

    if(is_premiere_running()[0]): 
        prApp.jsAddMarkers(beatsamplestoplace.tolist())
    elif(is_afterfx_running()[0]):
        aeApp.jsAddMarkers(beatsamplestoplace.tolist())
    elif(is_resolve_running()[0]):
        for beat in beatsamplestoplace:
            resApp = Resolve_Interface()
            resApp.addMarkerToCurrentTimeline(second=beat)
    info.set("Done!")

def clear_all_markers():
    if (is_premiere_running()[0] or is_afterfx_running()[0] or is_resolve_running()[0]):
        thread = Thread(target=remove_marks)
        thread.daemon = True
        thread.start()

def remove_marks():
    info.set("Removing markers...")
    root.update()
    if(is_premiere_running()[0]): 
        prApp.jsClearAllMarkers()
    elif(is_afterfx_running()[0]):
        aeApp.jsClearAllMarkers()
    elif(is_resolve_running()[0]):
        resApp = Resolve_Interface()
        resApp.clearAllMarkers()
    info.set("Done!")

def obtain_data_from_file():
    global data, beatsamples
    info.set("Reading file from source...")
    root.update()
    
    data, samplerate = librosa.load(path=path.get(), sr=SAMPLE_RATE, mono=True)
    
    info.set("Getting beat positions...")
    root.update()
    
    tempo, beatsamples = librosa.beat.beat_track(y=data, units="time", sr=SAMPLE_RATE)
    
    info.set("Displaying preview")
    root.update()

    data = numpy.asfortranarray(data)

def child_window_setup():
    global newWindow
    newWindow = tk.Toplevel(root)
    newWindow.title("Marker placement")
    newWindow.geometry("1000x380")

    canvas = tk.Canvas(newWindow, width=1000, height=300, bg="white")
    updateButton = ttk.Button(newWindow, text="Update markers", command=update_markers)
    playButton = ttk.Button(newWindow, text="Play", command=play_preview)

    # Draw the waveform 
    stepsize = int(len(data[:SAMPLE_RATE * 10]) / 1000)
    buffer = [int(x * 130 + 210) for x in data[:SAMPLE_RATE * 10:stepsize]]
    for i in range(len(buffer)-1):
        canvas.create_line(i, buffer[i], i + 1, buffer[i+1], fill="black")

    # Draw markers 
    for i in range(beatsamples.size):
        beat = beatsamples[i]
        
        if beat < 10:
            canvas.create_rectangle((beat*100 - 8, 90, beat*100 + 8, 110), fill="green", tags="marker") 

    canvas.pack()
    updateButton.pack()
    playButton.pack()

def retreive_and_preview():

    obtain_data_from_file()
    child_window_setup()

def select_file():
    global data
    global beatsamples
    global newWindow

    file_path = filedialog.askopenfilename(
        initialdir=os.path.expanduser("~"),
        title='Select an audio file',
        filetypes=[('Audio files', ['*.wav', '*.mp3', '*.flac', '*.ogg', '*.aiff']), ('All files', '.*')]
    )

    path.set(file_path) 

    thread = Thread(target=retreive_and_preview)
    thread.daemon = True
    thread.start()

def callback(in_data, frame_count, time_info, status):
    global playpos
    chunk = data[playpos:playpos+frame_count]
    playpos += frame_count
    if playpos >= SAMPLE_RATE*10:
        return (chunk, pyaudio.paComplete)
    return (chunk, pyaudio.paContinue)

def play_preview():
    global stream, iid
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=SAMPLE_RATE, output=True, stream_callback=callback)
    thread = Thread(target=track_line)
    thread.daemon = True
    thread.start()
    stream.start_stream()
    iid = newWindow.children["!canvas"].bind("<Button-1>", on_left_click)
    
def on_left_click(event):
    if 100 <= event.y <= 300:
        playpos_param.set(event.x)
        changepos.set(True)

def track_line():
    global newWindow
    global playpos
    global stream
    if changepos.get():
        playpos = int(playpos_param.get()/999*SAMPLE_RATE*10)
        changepos.set(False)
    position = int(playpos*999/SAMPLE_RATE/10)
    newWindow.children["!canvas"].delete("line")
    newWindow.children["!canvas"].create_line(position, 120, position, 300, fill="red", tags="line")
    newWindow.update()
    if (stream.is_active()): newWindow.after(10, track_line)
    else: 

        stream.close()
        playpos = 0
        newWindow.children["!canvas"].delete("line")
        newWindow.children["!canvas"].unbind("<Button-1>", iid)

def update_markers():
    global beatsamples
    global newWindow

    # Delete all markers from the canvas
    newWindow.update()
    canvas = newWindow.children["!canvas"]
    canvas.delete("marker")

    # Place markers from the first ten seconds as little rectangles on the canvas, beatsamples are in seconds
    # according to the new values from the sliders
    for beat in beatsamples[offsetvar.get()::everyvar.get()]:
        if beat < 10:
            canvas.create_rectangle((beat*100 - 8, 90, beat*100 + 8, 110), fill="green", tags="marker")
    newWindow.update()

###########################################
###########################################
###########################################
# Functions to check if apps are running
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

###########################################
###########################################
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
# An interface to actually call those commands. 
class AE_JSInterface(object):
    
    def __init__(self, aeVersion = "", returnFolder = ""):
        self.aeWindowName = "Adobe After Effects"
        self.aeCom = AE_JSWrapper(aeVersion, returnFolder) # Create wrapper to handle JSX

    def openAE(self):
        self.aeCom.openAE()

    def jsAddMarkers(self, list):
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
    
    def jsClearAllMarkers(self):
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

    def jsAddMarkers(self, list):
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

    def jsClearAllMarkers(self):
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
    
    def addMarkerToCurrentTimeline(self, second, color = "Blue"):
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
        frame = int(second * framerate)
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

###########################################
###########################################
newWindow = None
playpos = 0
p = pyaudio.PyAudio()
stream = None

if (is_afterfx_running()): aeApp = AE_JSInterface()
else: aeApp = None

if (is_premiere_running()): prApp = PR_JSInterface()
else: prApp = None

root = tk.Tk()
root.title("AutoMarker")

# Get the window width and height
window_width = root.winfo_reqwidth()
window_height = root.winfo_reqheight()

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the position of the left and top borders of the window
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)

# Set the geometry of the window
root.geometry("+{}+{}".format(position_right, position_top))

style = ttk.Style()
if WINDOWS_SYSTEM:
    style.theme_use(themename='xpnative')
else:
    style.theme_use(themename='aqua')
mainframe = tk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

runvar = tk.StringVar()
path = tk.StringVar()
info = tk.StringVar()
everyvar = tk.IntVar(value=1)
offsetvar = tk.IntVar(value=0)
playpos_param = tk.IntVar(value=0)
changepos = tk.BooleanVar(value=False)

authorLabel = tk.Label(mainframe, text="by acrilique")
runvarLabel = tk.Label(mainframe, textvariable=runvar)
pathLabel = tk.Label(mainframe, textvariable=path)
infoLabel = tk.Label(mainframe, textvariable=info)
readmeButton = ttk.Button(mainframe, text="Readme", command=lambda: os.startfile(os.path.join(basedir, 'README.md')))
selectFileButton = ttk.Button(mainframe, text="Select audio file", command=select_file, width=40)
createMarkersButton = ttk.Button(mainframe, text="Create markers", command=auto_beat_marker, width=40)# , command=auto_beat_marker
removeMarkersButton = ttk.Button(mainframe, text="Remove markers", command=clear_all_markers, width=40)                                                                                                                                                                 
everyLabel = tk.Label(mainframe, text="Place markers every x beats")
everyScale = ttk.LabeledScale(mainframe, variable=everyvar, from_=1, to=16, compound='bottom')
offsetLabel = tk.Label(mainframe, text="Offset first beat")
offsetScale = ttk.LabeledScale(mainframe, variable=offsetvar, from_=0, to=16, compound='bottom')
versionLabel = tk.Label(mainframe, text="v0.3.3")

everyScale.update()
offsetScale.update()

authorLabel.grid(column=1, row=0, sticky=(tk.W))
readmeButton.grid(column=1, row=0, sticky=(tk.E))
pathLabel.grid(column=1, row=1, sticky=(tk.W, tk.E))
selectFileButton.grid(column=1, row=2, sticky=(tk.W, tk.E))
createMarkersButton.grid(column=1, row=3, sticky=(tk.W, tk.E))
removeMarkersButton.grid(column=1, row=4, sticky=(tk.W, tk.E))
everyLabel.grid(column=1, row=5, sticky=(tk.W))
everyScale.grid(column=1, row=6, sticky=(tk.W, tk.E))
offsetLabel.grid(column=1, row=7, sticky=(tk.W))
offsetScale.grid(column=1, row=8, sticky=(tk.W, tk.E))
runvarLabel.grid(column=1, row=9, sticky=(tk.W))
infoLabel.grid(column=1,row=9, sticky=(tk.E))
versionLabel.grid(column=1, row=10, sticky=(tk.E))


for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

icon = tk.PhotoImage(file=os.path.join(basedir, "icon.png"))
root.tk.call('wm', 'iconphoto', root._w, icon)
root.after(0, update_runvar)

root.mainloop()