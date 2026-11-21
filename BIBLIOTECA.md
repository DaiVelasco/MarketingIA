# Biblioteca audiovisual de las campañas

El bibliotecario ayuda a encontrar una **acción, un archivo y un segundo** para el guion. Por ejemplo, para un reel en el que una mano alisa una película sobre una carrocería, Dirección puede buscar el término `lámina`, abrir el tramo recomendado y decidir si conviene un plano en movimiento o un fotograma para Canva.

## Depositar un video

Dentro de `campanas/<cuenta>/<fecha>/Videos del proyecto - Reel de Instagram/`, coloca el material de cámara en `01 - Videos crudos` y las piezas que servirán de referencia en `02 - Referencias`. El bibliotecario vigila estas dos entradas en las campañas del proyecto, incluidas sus subcarpetas. Los másteres completos conservan su carpeta de entrega `03 - Videos terminados`.

Admite MP4, MOV, M4V, MKV, WebM, AVI, MTS, M2TS, MPG, MPEG, MXF y 3GP. El proceso espera a que el tamaño y la fecha de modificación se mantengan estables al menos 15 segundos. FFprobe obtiene duración, dimensiones y pistas. El agente compara el SHA-256 con el de otros archivos de la misma cuenta para recuperar la ficha si ya hay una copia idéntica. El índice conserva ambas ubicaciones.

Para un video nuevo, FFmpeg extrae entre 3 y 18 fotogramas repartidos a lo largo del archivo. La sesión de Codex del equipo recibe la plancha, sus tiempos y las observaciones sonoras para describir los planos. La ficha indica qué se ve, cuándo, para qué pieza sirve y qué podría estorbar al recortar, como un rótulo incrustado.

## Comprobar el sonido

FFprobe identifica si existe pista de audio. Cuando la encuentra, FFmpeg toma muestras de la primera pista y registra inicio, fin y pico de señal. Con los ajustes iniciales toma hasta tres ventanas de siete segundos, según la duración del archivo. Si una muestra dio silencio digital, la observación se limita a esa ventana. La presencia de señal por sí sola deja pendiente distinguir música, efectos o voz. El resultado de las nuevas clasificaciones se conserva en `ficha.observacion_audio` del catálogo JSON.

Para obtener una frase orientativa en los videos con posible habla, instala en la otra máquina un entorno Python local con Whisper, PyTorch y NumPy, y guarda allí el modelo de Whisper que vayas a utilizar. Crea `.local/biblioteca-audio.json` en ese equipo y ajusta las dos rutas de este ejemplo a sus archivos reales. Pueden ser absolutas o relativas a la raíz del proyecto.

```json
{
  "habilitar_whisper": true,
  "idioma": "es",
  "python_whisper": ".local/whisper/Scripts/python.exe",
  "modelo_whisper": ".local/modelos/base.pt",
  "ventanas": 3,
  "segundos_por_ventana": 7,
  "timeout_ffmpeg": 15,
  "timeout_whisper": 65
}
```

El reconocimiento se ejecuta en la PC y la ficha conserva la frase con sus tiempos si el resultado es suficientemente claro. Para una cita pública, reproduce ese intervalo y comprueba las palabras. Puedes usar de 1 a 3 ventanas de 2 a 12 segundos, un límite de 3 a 30 segundos para extraer cada ventana y de 5 a 90 segundos por archivo para Whisper. Sin configuración adicional se mantiene el muestreo básico de FFmpeg. Un tiempo agotado o un entorno Whisper no disponible queda registrado como incidencia de audio y el análisis visual continúa.

## Elegir material para un reel o un carrusel

Desde la carpeta raíz del proyecto se puede consultar la cuenta y buscar tanto una acción como una herramienta, un tema o un archivo.

```powershell
python biblioteca.py estado
python biblioteca.py buscar cuenta.demo "aplicador"
python biblioteca.py buscar cuenta.demo "detalle-panel.mp4"
```

También se puede abrir `biblioteca/<cuenta>/CATALOGO.md`. Su índice enlaza al video y muestra el mejor tramo. Debajo de cada archivo están las escenas, las limitaciones, la familia y los usos sugeridos. `catalogo.json` contiene además la ruta relativa, la huella, los metadatos técnicos y el estado. La búsqueda ignora mayúsculas y minúsculas y compara el término con el contenido de cada ficha de esa cuenta.

En el traspaso al editor o a Diseño, anota el nombre exacto, el minuto o segundo de entrada y salida, la acción que debe conservarse y si se va a usar como toma, fotograma o referencia de estilo. Abre el intervalo completo antes de fijar el corte para comprobar si un subtítulo que aparece entre dos muestras tapa la mano o el detalle elegido. Revisa la familia si aparecen varias versiones de un testimonio.

## Instalar el monitor en otra PC con Windows

1. Clona el repositorio en una carpeta de trabajo. Instala Python 3.11 o superior con `python.exe` y `pythonw.exe`, FFmpeg con `ffmpeg` y `ffprobe`, y el cliente de Codex. Comprueba desde PowerShell las versiones y la sesión de la cuenta que ejecutará el monitor.

   ```powershell
   python --version
   Get-Command pythonw.exe, codex.exe
   ffmpeg -version
   ffprobe -version
   codex login status
   ```

2. Si FFmpeg está en una carpeta particular, configura `MARKETINGIA_FFMPEG` y `MARKETINGIA_FFPROBE` con las rutas de los ejecutables, o coloca ambos en `.local/` del proyecto. El cliente de Codex debe poder ejecutar el análisis de imágenes con la sesión del usuario.

3. Desde la carpeta que contiene `biblioteca.py`, ejecuta el instalador. Registra **MarketingIA - Biblioteca audiovisual** en Inicio de la cuenta Windows y solicita el primer arranque en segundo plano. El monitor se inicia también al volver a iniciar sesión. Si mueves el proyecto, ejecuta el instalador desde su nueva ubicación.

   ```powershell
   .\herramientas\instalar-bibliotecario.ps1
   ```

4. Copia un video a una de las dos entradas de una campaña y consulta `python biblioteca.py estado`. Puede aparecer primero `en_copia` y después `clasificado`. La máquina debe permanecer encendida y con la sesión iniciada para atender nuevas llegadas. Al arrancar, el monitor revisa las carpetas, por lo que también recoge archivos que llegaron mientras estaba apagado.

Para comprobar la ejecución en primer plano se puede usar `python biblioteca.py vigilar`. El monitor mantiene un bloqueo por proyecto para evitar dos vigilancias simultáneas. Para un único barrido usa `python biblioteca.py procesar`; si acaba de descubrir los archivos, repite el barrido una vez transcurridos los 15 segundos de estabilidad. En los comandos de depuración, `--raiz RUTA` o `--codex RUTA_AL_EJECUTABLE` van antes de la acción.

## Estados, correcciones y traslado

| Estado | Interpretación |
|---|---|
| `en_copia` | La ruta es nueva o sus atributos cambiaron. Se espera una copia estable. |
| `clasificado` | La ficha está disponible para Dirección, Guion, Edición y Diseño. |
| `reintento` | Una herramienta o la clasificación no pudieron completar el trabajo. Revisa la incidencia en el catálogo y la sesión del cliente. El monitor vuelve a intentarlo con esperas crecientes. |
| `ilegible` | FFprobe no pudo abrir el contenido como video con duración válida. Al sustituir el archivo, el monitor vuelve a examinarlo. |
| `retirado` | La ruta dejó de existir. El catálogo consultable conserva como selecciones las rutas disponibles. |

Un especialista puede aportar fichas ya revisadas de los videos en `02 - Referencias`. Prepara un archivo JSON con una lista de objetos. Cada uno contiene el nombre exacto en `archivo`, los campos de texto `tema`, `resumen`, `mejor_tramo`, `audio`, `limitaciones` y `familia`, una lista `usos` y una lista `tramos`. Cada tramo lleva `inicio`, `fin` en segundos y `detalle`. La importación comprueba el archivo, la duración y el contenido de la ficha.

```powershell
python biblioteca.py importar campanas/cuenta.demo/2026-11-21 ruta/al/grupo.json
```

La biblioteca se inicia vacía. El primer escaneo crea la base local en `biblioteca/`. Para trasladar un catálogo propio entre equipos, detén el monitor y copia por un canal privado la biblioteca y sus campañas manteniendo las mismas rutas relativas. Reinicia el monitor en destino. El acceso directo de Inicio se instala en cada PC. [Guía de operación](OPERACION.md) · [Memoria editorial](APRENDIZAJE.md)
