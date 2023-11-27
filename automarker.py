# AutoMarker by acrilique.
################################
# Licensed under GNU GPL v3.0 #
################################

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from threading import Thread
import librosa
import pyaudio
import pymiere
import os
import numpy
import sys
import re
import json
import subprocess
from distutils.version import StrictVersion
import platform

sample_rate = 44100
###############################
###############################
###############################
###############################

if platform.system().lower() == "windows":
    WINDOWS_SYSTEM = True
    import winreg as wr  # python 3
else:
    # if not windows, assume it is a macOS
    WINDOWS_SYSTEM = False

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
    with open(os.path.join(basedir, 'flag.txt'), 'r') as flag_file:
        flag_content = flag_file.read().strip()
except FileNotFoundError:
    # If the file is not found, treat it as not installed
    flag_content = "not_installed"

if flag_content == "not_installed":
    # Execute the batch script
    if WINDOWS_SYSTEM:
        subprocess.run([os.path.join(basedir, 'extension_installer_win.bat')])
    else:
        subprocess.run([os.path.join(basedir, 'extension_installer_mac.sh')])
    # Update the flag.txt file to indicate that the script has been executed, erasing old text
    with open('flag.txt', 'w') as flag_file:
        flag_file.write("installed")

CREATE_NO_WINDOW = 0x08000000
PREMIERE_PROCESS_NAME = "adobe premiere pro.exe" if WINDOWS_SYSTEM else "Adobe Premiere Pro"
CEPPANEL_PROCESS_NAME = "CEPHtmlEngine.exe" if WINDOWS_SYSTEM else "CEPHtmlEngine"

###############################
###############################
###############################
###############################

def update_runvar():
    if(is_premiere_running()[0]):
        runvar.set("Premiere is running!")
    else:
        runvar.set("Premiere isn't running :(")
    root.after(1000, update_runvar)

def auto_beat_marker():
    if (is_premiere_running()[0]):
        thread = Thread(target=place_marks)
        thread.daemon = True
        thread.start()

def place_marks():
    global data
    global beatsamples

    every = everyvar.get()
    offset = offsetvar.get()
    if (every > 1):
        # Add only every x beats
        beatsamples = beatsamples[offset::every]
    
    info.set("Placing markers...")
    root.update()
    end_of_sequence = pymiere.objects.app.project.activeSequence.end
    # Create markers using pymiere
    for sample in beatsamples:
        if sample < end_of_sequence:
            pymiere.objects.app.project.activeSequence.markers.createMarker(sample)
    info.set("Done!")

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

    info.set("Reading file from source...")
    root.update()
    
    data, samplerate = librosa.load(path=path.get(), sr=sample_rate, mono=True)
    
    info.set("Getting beat positions...")
    root.update()
    
    tempo, beatsamples = librosa.beat.beat_track(y=data, units="time", sr=sample_rate)
    
    info.set("Displaying preview")
    root.update()

    data = numpy.asfortranarray(data)

    newWindow = tk.Toplevel(root)
    newWindow.title("Marker placement")
    newWindow.geometry("1000x380")

    canvas = tk.Canvas(newWindow, width=1000, height=300, bg="white")
    updateButton = ttk.Button(newWindow, text="Update markers", command=update_markers)
    playButton = ttk.Button(newWindow, text="Play", command=play_preview)

    # Draw the waveform 
    stepsize = int(len(data[:samplerate * 10]) / 1000)
    buffer = [int(x * 130 + 210) for x in data[:samplerate * 10:stepsize]]
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

def callback(in_data, frame_count, time_info, status):
    global playpos
    chunk = data[playpos:playpos+frame_count]
    playpos += frame_count
    if playpos >= sample_rate*10:
        return (chunk, pyaudio.paComplete)
    return (chunk, pyaudio.paContinue)

def play_preview():
    global stream, iid
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True, stream_callback=callback)
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
        playpos = int(playpos_param.get()/999*sample_rate*10)
        changepos.set(False)
    position = int(playpos*999/sample_rate/10)
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
# Functions to check if premiere is running
def is_premiere_running():
    """
    Is there a running instance of the Premiere Pro app on this machine ?

    :return: (bool) process is running, (int) pid
    """
    return exe_is_running(PREMIERE_PROCESS_NAME)

def start_premiere(use_bat=False):
    raise SystemError("Could not guaranty premiere started")

def exe_is_running(exe_name):
    """
    List processes by name to know if one is running

    :param exe_name: (str) exact name of the process (ex : 'pycharm64.exe' for windows or 'Safari' for mac)
    :return: (bool) process is running, (int) pid
    """
    pids = _get_pids_from_name(exe_name)
    if len(pids) == 0:
        return False, None
    if len(pids) > 1:
        raise OSError("More than one process matching name '{}' were found running (pid: {})".format(exe_name, pids))
    return True, pids[0]

def count_running_exe(exe_name):
    """
    List processes by name to know how many are running

    :param exe_name: (str) exact name of the process (ex : 'pycharm64.exe' for windows or 'Safari' for mac)
    :return: (int) Number of process with given name running
    """
    return len(_get_pids_from_name(exe_name))

def get_last_premiere_exe():
    """
    Get the executable path on disk of the last installed Premiere Pro version

    :return: (str) path to executable
    """
    get_last_premiere_exe_func = _get_last_premiere_exe_windows if WINDOWS_SYSTEM else _get_last_premiere_exe_mac
    return get_last_premiere_exe_func()

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
        return [int(re.findall("   ([0-9]{1,6}) [a-zA-Z]", l)[0]) for l in matching_lines]
    else:
        # use pgrep UNIX command to filter processes by name
        try:
            output = subprocess.check_output(["pgrep", process_name])
        except subprocess.CalledProcessError:  # pgrep seems to crash if the given name is not a running process...
            return list()
        # parse output lines
        lines = output.strip().splitlines()
        return list(map(int, lines))

# ----- platform specific functions -----
def _get_last_premiere_exe_windows():
    """
    WINDOWS ONLY
    Get the executable path on disk of the last installed Premiere Pro version using windows registry

    :return: (str) path to executable
    """
    premiere_versions = _get_installed_softwares_info("adobe premiere pro")
    if not premiere_versions:
        raise OSError("Could not find an Adobe Premiere Pro version installed on this computer")
    # find last installed version
    last_version_num = sorted([StrictVersion(v["DisplayVersion"]) for v in premiere_versions])[-1]
    last_version_info = [v for v in premiere_versions if v["DisplayVersion"] == str(last_version_num)][0]
    # search actual exe path
    base_path = last_version_info["InstallLocation"]
    build_year = last_version_info["DisplayName"].split(" ")[-1]
    wrong_paths = list()
    for folder_name in ["Adobe Premiere Pro CC {}", "Adobe Premiere Pro {}", ""]:  # different versions formatting
        exe_path = os.path.join(base_path, folder_name.format(build_year), "Adobe Premiere Pro.exe")
        if not os.path.isfile(exe_path):
            wrong_paths.append(exe_path)
            continue
        wrong_paths = list()
        break
    if len(wrong_paths) != 0:
        raise IOError("Could not find Premiere executable in '{}'".format(wrong_paths))
    return exe_path

def _get_last_premiere_exe_mac():
    """
    MACOS ONLY
    Get the executable path on disk of the last installed Premiere Pro version using macOS System Profiler

    :return: (str) path to executable
    """
    # list all installed app to a json datastructure
    output = subprocess.check_output(["system_profiler", "-json", "SPApplicationsDataType"])
    apps_data = json.loads(output)["SPApplicationsDataType"]
    # filter Premiere pro installed versions
    premiere_apps = [data for data in apps_data if "adobe premiere pro" in data["_name"].lower()]
    if not premiere_apps:
        raise OSError("Could not find an Adobe Premiere Pro version installed on this computer")
    # get last app version path
    premiere_apps.sort(key=lambda d: d["version"], reverse=True)
    return premiere_apps[0]["path"]

def _get_installed_softwares_info(name_filter, names=["DisplayVersion", "InstallLocation"]):
    """
    WINDOWS ONLY
    Looking into Uninstall key in Windows registry, we can get some infos about installed software

    :param name_filter: (str) filter software containing this name
    :return: (list of dict) info of software found
    """
    reg = wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE)
    key = wr.OpenKey(reg, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    apps_info = list()
    # list all installed apps
    for i in range(wr.QueryInfoKey(key)[0]):
        subkey_name = wr.EnumKey(key,i)
        subkey = wr.OpenKey(key, subkey_name)
        try:
            soft_name = wr.QueryValueEx(subkey, "DisplayName")[0]
        except EnvironmentError:
            continue
        if name_filter.lower() not in soft_name.lower():
            continue
        apps_info.append(dict({n: wr.QueryValueEx(subkey, n)[0] for n in names}, DisplayName=soft_name))
    return apps_info
###########################################
###########################################
###########################################

root = tk.Tk()
root.title("AutoMarker")
newWindow = None
playpos = 0
p = pyaudio.PyAudio()
stream = None

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
style.theme_use(themename='xpnative')

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
createMarkersButton = ttk.Button(mainframe, text="Create markers", command=auto_beat_marker, width=40)
everyLabel = tk.Label(mainframe, text="Place markers every x beats")
everyScale = ttk.LabeledScale(mainframe, variable=everyvar, from_=1, to=16, compound='bottom')
offsetLabel = tk.Label(mainframe, text="Offset first beat")
offsetScale = ttk.LabeledScale(mainframe, variable=offsetvar, from_=0, to=16, compound='bottom')
versionLabel = tk.Label(mainframe, text="v0.2.0")

everyScale.update()
offsetScale.update()

authorLabel.grid(column=1, row=0, sticky=(tk.W))
readmeButton.grid(column=1, row=0, sticky=(tk.E))
pathLabel.grid(column=1, row=1, sticky=(tk.W, tk.E))
selectFileButton.grid(column=1, row=2, sticky=(tk.W, tk.E))
createMarkersButton.grid(column=1, row=3, sticky=(tk.W, tk.E))
everyLabel.grid(column=1, row=4, sticky=(tk.W))
everyScale.grid(column=1, row=5, sticky=(tk.W, tk.E))
offsetLabel.grid(column=1, row=6, sticky=(tk.W))
offsetScale.grid(column=1, row=7, sticky=(tk.W, tk.E))
runvarLabel.grid(column=1, row=8, sticky=(tk.W))
infoLabel.grid(column=1,row=8, sticky=(tk.E))
versionLabel.grid(column=1, row=9, sticky=(tk.E))


for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

root.iconbitmap(os.path.join(basedir, "icon.ico"))
root.after(0, update_runvar)

root.mainloop()