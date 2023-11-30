
## AutoMarker

AutoMarker is a Python-based GUI application that allows users to place markers on a Premiere Pro sequence, an After Effects composition or a Davinci Resolve Studio timeline based on a music file's tempo. This is useful for placing clips faster when you want them to be related to the music that is playing. The application uses the librosa library to detect beats in the audio file.

# Features

 - Detects beats in an audio file and places markers.

 - Supports audio files in formats such as .wav, .mp3, .flac, .ogg, and .aiff.

 - Allows users to specify the frequency of markers and an offset for the first beat.

 - Checks if any of the apps are running and provides feedback to the user.

 - New: preview the first 10 seconds of your markers before placing them, and delete all your placed markers with just one click!

# Installation

AutoMarker is packaged as a standalone executable using PyInstaller. To obtain the latest release, get it for cheap on Gumroad (in the form of .exe or .dmg).

# Usage

If you installed using the packaged app, you can launch it from your system's application menu. The application will open in a new window. The first time you open it after installing it, it will install the necessary Premiere Pro extension called "AutoMarker". 

To use AutoMarker, follow these steps:

 1. Click the "Select audio file" button to choose an audio file.

 2. If Premiere, AfterFX or Resolve is running, click the "Create markers" button to place markers on the active sequence, composition or timeline based on the audio file's tempo. 

 3. You can adjust the frequency of markers and the offset for the first beat using the sliders.

 4. In Premiere Pro and Davinci Resolve, your sequence/timeline need's to have a duration equal or greater than the input audio file's. For that, please import the file, or anything else, to the sequence/timeline before placing the markers.

It is important to note that having more than 1 of the supported apps active at the same time can cause unexpected behaviour. If Premiere is active, it will be the one being used. If not, After Effects, and then Resolve. I'm thinking about implementing an input for the user to choose which app they want to put the markers to.

# Troubleshooting

If you encounter any issues while using AutoMarker, ensure that Adobe Premiere Pro is installed and running. If the problem persists, please get in touch and I'll try to check it as soon as I'm free. I'm also open to feature suggestions!

# Contact

For any questions or concerns, please open an issue or contact me personally at lluc.simo5@gmail.com

I get a lot of emails so insist if you see that I dont answer.

## AutoMarker

AutoMarker es una aplicación GUI basada en Python que permite a los usuarios colocar marcadores en una secuencia de Premiere Pro, una composición de After Effects o una línea de tiempo de Davinci Resolve Studio basada en el tempo de un archivo de música. Esto es útil para colocar clips más rápido cuando se desea que estén relacionados con el ritmo de la música que se quiere utilizar. La aplicación hace uso de la biblioteca de código abierto librosa para detectar beats en el archivo de audio.

# Características

 - Detecta beats en un archivo de audio y coloca marcadores.

 - Admite archivos de audio en formatos como .wav, .mp3, .flac, .ogg y .aiff.

 - Permite a los usuarios especificar la frecuencia de los marcadores y un desplazamiento para el primer tiempo.

 - Comprueba si cualquiera de los tres programas se está ejecutando y proporciona comentarios al usuario.

 - Nuevo: obtén una vista previa de los primeros 10 segundos de sus marcadores antes de colocarlos y elimina todos los marcadores colocados con solo un clic.

# Instalación

AutoMarker está empaquetado como un ejecutable independiente mediante PyInstaller. Para obtener la última versión, consíguela por por lo que cuesta un café en Gumroad (en forma de .exe o .dmg).

# Uso

Si la instalaste utilizando la aplicación empaquetada, puedes iniciarla desde el menú de aplicaciones de su sistema. La aplicación se abrirá en una nueva ventana. La primera vez que la ejecutes después de instalarla, se realizará la instalación de la extensión de Premiere Pro "AutoMarker", la cuál permite a AutoMarker ejecutar comandos en Premiere.

Para utilizar AutoMarker, sigue estos pasos:

 1. Haz clic en el botón "Seleccionar archivo de audio" para elegir un archivo de audio.

 2. Si se está ejecutando Premiere, AfterFX o Resolve, haz clic en el botón "Crear marcadores" para colocar marcadores en la secuencia activa según el tempo del archivo de audio.

 3. Puedes ajustar la frecuencia de los marcadores y el desplazamiento del primer tiempo utilizando los controles deslizantes.

 4. En Premiere Pro y Davinci Resolve, tu secuencia/línea de tiempo necesita tener una duración igual o mayor que la del archivo de audio de entrada. Para eso, importa el archivo, o cualquier otra cosa, a la secuencia/línea de tiempo antes de colocar los marcadores.

Es importante tener en cuenta que tener activas más de una de las aplicaciones compatibles al mismo tiempo puede provocar un comportamiento inesperado. Si Premiere está activo, será el que se utilice. Si no, After Effects y luego Resolve. Estoy pensando en implementar un input para que el usuario elija en qué app quiere poner los marcadores.

# Solución de problemas

Si encuentras algún problema al utilizar AutoMarker, asegúrate de que la aplicación en la que quieres poner los marcadores esté instalada y ejecutándose. Si el problema persiste, ponte en contacto conmigo e intentaré comprobarlo en cuanto esté libre. ¡También estoy abierto a sugerencias de funciones!

# Contacto

Si tienes alguna pregunta o inquietud, contáctame personalmente en lluc.simo5@gmail.com.

Recibo muchos correos, así que insiste si ves que no respondo.