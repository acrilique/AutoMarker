import sys
from subprocess import run

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_script.py <version>")
        return

    version = sys.argv[1]
    print("Building AutoMarker version: " + version + " for Windows...")
    # run pyinstaller
    run(["pyinstaller", "automarker_win.spec", "--noconfirm"])
    # write script.nsi file with version
    with open("script.nsi", "w") as f:
        f.write(
        f""" 
; The name of the installer
Name "AutoMarker"

; The file to write
OutFile "dist\\AutoMarker_{version}.exe"

; Request application privileges for Windows Vista and higher
RequestExecutionLevel admin

; Build Unicode installer
Unicode True

; The default installation directory
InstallDir $PROGRAMFILES\\AutoMarker

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\\NSIS_Example2\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AutoMarker" "Install_Dir"

; Import modern ui
!include "MUI2.nsh"

;--------------------------------

; Pages

!define MUI_ICON "icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "icon.bmp"
!define MUI_HEADERIMAGE_RIGHT
!define MUI_PAGE_HEADER_TEXT "Welcome to AutoMarker"
!define MUI_PAGE_HEADER_SUBTEXT "This wizard will guide you through the installation process."
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

;--------------------------------

; The stuff to install
Section "AutoMarker (required)"

    SectionIn RO
    
    ; Set output path to the installation directory.
    SetOutPath $INSTDIR
    
    ; Put file there
    File /nonfatal /a /r "dist\\automarker\\*.*"

    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    ; Write the installation path into the registry
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AutoMarker" \\
                                    "DisplayName" "AutoMarker"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AutoMarker" \\
                                    "UninstallString" "$\\"$INSTDIR\\uninstall.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AutoMarker" \\
                                    "DisplayIcon" "$INSTDIR\\_internal\\icon.ico"
    
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

    CreateShortcut "$SMPROGRAMS\\AutoMarker.lnk" "$INSTDIR\\AutoMarker.exe"

SectionEnd

;--------------------------------


;--------------------------------

; Uninstaller

Section "Uninstall"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AutoMarker"

    ; Remove shortcuts, if any
    Delete "$SMPROGRAMS\\AutoMarker.lnk"

    ; Remove directories
    RMDir /r "$INSTDIR"

SectionEnd

"""
        )
    print("Building installer...")
    # run makensis
    run(["C:\\Program Files (x86)\\NSIS\\makensis.exe", "/V4", "script.nsi"])
    print("Done!")


if __name__ == "__main__":
    main()