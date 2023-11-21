# AutoMarker

AutoMarker is a Python-based GUI application that allows users to place markers on a Premiere Pro active sequence based on a music file's tempo. The application uses the librosa library to detect beats in the audio file and the pymiere library to interact with Adobe Premiere Pro.

## Features

- Detects beats in an audio file and places markers on a Premiere Pro active sequence.
- Supports audio files in formats such as .wav, .mp3, .flac, .ogg, and .aiff.
- Allows users to specify the frequency of markers and an offset for the first beat.
- Checks if Adobe Premiere Pro is running and provides feedback to the user.

## Installation

AutoMarker is packaged as a standalone executable using PyInstaller. This means that the user does not need to install Python or any dependencies to run the application.

To install AutoMarker, follow these steps:

1. Download the executable file for your operating system from the provided source.
2. Run the downloaded file to install AutoMarker.

## Usage

After installing AutoMarker, you can launch it from your system's application menu. The application will open in a new window.

To use AutoMarker, follow these steps:

1. Click the "Select audio file" button to choose an audio file.
2. If Adobe Premiere Pro is running, click the "Create markers" button to place markers on the active sequence based on the audio file's tempo.
3. You can adjust the frequency of markers and the offset for the first beat using the sliders.

## Troubleshooting

If you encounter any issues while using AutoMarker, ensure that Adobe Premiere Pro is installed and running. If the problem persists, please get in touch for further assistance.

## Contributing

We welcome contributions to AutoMarker. If you have a feature request, bug report, or want to improve the documentation, please submit an issue or pull request on our GitHub repository.

## License

AutoMarker is licensed under the MIT License. For more information, please refer to the LICENSE file in the repository.

## Contact

For any questions or concerns, please contact me personally at lluc.simo5@gmail.com