# AutoMarker

AutoMarker is a Python-based GUI application that allows users to place markers on a Premiere Pro active sequence based on a music file's tempo. This is useful for placing clips faster when you want them to be related to the music that is playing. The application uses the librosa library to detect beats in the audio file and the pymiere library to interact with Adobe Premiere Pro.

## Features

- Detects beats in an audio file and places markers on a Premiere Pro active sequence.
- Supports audio files in formats such as .wav, .mp3, .flac, .ogg, and .aiff.
- Allows users to specify the frequency of markers and an offset for the first beat.
- Checks if Adobe Premiere Pro is running and provides feedback to the user.

## Installation

AutoMarker is packaged as a standalone executable using PyInstaller and its source code is also available on Github. To obtain the latest release, get it for cheap on Gumroad (in the form of .exe or .dmg) or just install Python and run the script! You will need librosa and pymiere libraries, and both are available to install using pip. My advice if you are new using python is creating a venv first, and then activating it and installing the libraries there.

## Usage

If you installed using the packaged app, you can launch it from your system's application menu. The application will open in a new window.

To use AutoMarker, follow these steps:

1. Click the "Select audio file" button to choose an audio file.
2. If Adobe Premiere Pro is running, click the "Create markers" button to place markers on the active sequence based on the audio file's tempo.
3. You can adjust the frequency of markers and the offset for the first beat using the sliders.

## Troubleshooting

If you encounter any issues while using AutoMarker, ensure that Adobe Premiere Pro is installed and running. If the problem persists, please open an issue and I'll try to check it as soon as I'm free.

## Contributing

I welcome contributions to AutoMarker. If you have a feature request, bug report, or want to improve the documentation, please submit an issue or pull request on our GitHub repository.

## License

AutoMarker is licensed under the GNU General Public License 3.0. Check the LICENSE.md file for specific information about licensing.

## Contact

For any questions or concerns, please open an issue or contact me personally at lluc.simo5@gmail.com
I get a lot of emails so insist if you see that I dont answer.