# Sonido para la edición de video

Contenidos anota dónde entra la música, dónde debe apartarse de una frase y qué acción merece un efecto. En el reel de las llaves, por ejemplo, la música baja para que se oiga el mosquetón al cerrarse. Edición mezcla las voces limpias, la música autorizada y los efectos sincronizados con la imagen.

Desactiva el audio de los crudos y de la sincronización labial cuando la voz procede de otra pista. Si necesitas el diálogo de un crudo, aísla la voz y escucha el final de las palabras al ajustar la reducción de ruido. Si necesitas el sonido de una acción, recorta ese gesto, limpia el fondo y sitúalo en el cuadro correspondiente. Quita también las camas continuas de ambiente que traigan los proyectos reutilizados.

Revisión escucha la voz y el acompañamiento por separado y después reproduce el MP4 completo. Comprueba la dicción con música, las pausas entre frases, los ataques de los efectos y la cola de la placa. Si detecta ventiladores, tráfico, conversaciones ajenas o una voz guía duplicada, anota la pista y el segundo para que Edición corrija la fuente.

| Herramienta en la orden | Cuándo usarla | Evidencia que entrega Edición |
| --- | --- | --- |
| Pixabay | Para Konduce, buscar una instrumental que acompañe el ritmo de la locución y permita usar la pieza en la campaña. [Catálogo musical](https://pixabay.com/music/search/) | Título, autor, ficha del tema, licencia y archivo elegido. |
| `Openverse` | Consultar este cliente en proyectos que utilicen ese catálogo para efectos grabados. Admite CC0, marca de dominio público y CC BY. | ID, autor, licencia con versión, ficha de origen y atribución de los archivos usados. |
| `real-sfx` | Indexar grabaciones propias o licenciadas, elegir un fragmento y situar su ataque o su pico en el montaje. | Hoja de eventos resuelta, pista de efectos y tiempos. |
| `earshot` | Crear un acento para una animación, un obturador o un sonido de interfaz. El motor local admite descripciones en inglés y una semilla. | WAV, descripción y semilla. Identificar la fuente como generada. |
| `diseno-sonido` | Colocar efectos por papel y posición, reducir su presencia sobre la voz y medir la mezcla. | Capa de efectos, mezcla e informe con los tiempos, LUFS y pico real. |
| `real-sound` | Analizar grabaciones y revisar una banda construida con material licenciado. | Análisis del archivo y, si hay fuentes externas, créditos del material utilizado. |

El expediente de cada edición conserva el origen de los sonidos y las órdenes que atendió cada herramienta. Para CC BY, incluir el crédito, el enlace al recurso y a la licencia e indicar las modificaciones. Si el catálogo devuelve un error, registrarlo y usar una grabación propia o un efecto generado cuando encaje.

## Ejecutar en MarketingIA

Desde la raíz del proyecto, `python herramientas/audio_video.py` resuelve el intérprete aislado, FFmpeg y las skills. En PowerShell:

```powershell
python herramientas/audio_video.py real-sfx build_index
python herramientas/audio_video.py real-sfx search --query shutter
python herramientas/audio_video.py earshot make "a camera shutter" --seed 7 -o obturador.wav
python herramientas/audio_video.py diseno-sonido mezclar eventos.json --dur 30 --voz voz-alineada.wav --salida mezcla.wav
python herramientas/audio_video.py real-sound analyze mezcla.wav
```

El banco predeterminado es `.local/sonido/banco/`. `grabaciones/` contiene el material propio para real-sfx y `openverse/` contiene sus descargas y manifiesto. Para usar un sonido elegido con diseno-sonido, colócalo en la subcarpeta de su papel, por ejemplo `clic/obturador.wav`. Una entrada de `eventos.json` como `[[1.266667, "clic", {}]]` sitúa el gesto en el fotograma 38 de un montaje a 30 fps, contando desde cero. Al mezclar con voz, prepara esa pista alineada con el montaje y con silencio hasta el final. Puedes seleccionar un banco por proyecto con la variable `SONIDOS_DIR`.

## Acceso a Openverse desde el editor

Openverse permite buscar de forma anónima. Si el editor recibe `403` junto con `cf-mitigated: challenge`, Cloudflare está presentando una verificación antes de la respuesta de la API. El editor muestra la ruta y el **Ray ID** y termina con error para que Edición pueda registrar el bloqueo. Si también sucede al pedir el token, envía a **openverse@wordpress.org** el método, la ruta, la fecha y hora UTC y el Ray ID, y solicita que revisen el acceso de la aplicación. [Diagnóstico de Cloudflare](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/detect-response/) · [Contacto y API de Openverse](https://api.openverse.org/v1/)

Para obtener credenciales, registra una sola vez la aplicación con un nombre único, una descripción y un correo que puedas verificar. Desde PowerShell, el siguiente ejemplo conserva la respuesta en una variable. Guarda el par devuelto en tu gestor de contraseñas y abre el enlace que envía Openverse al correo. [Registro oficial y autenticación](https://api.openverse.org/v1/#tag/auth)

```powershell
$datos = @{
    name = Read-Host 'Nombre único de tu aplicación'
    description = 'Selección de efectos de sonido con licencia para la edición de videos de Konduce'
    email = Read-Host 'Correo donde recibirás el enlace de verificación'
}
$app = Invoke-RestMethod -Method Post -Uri 'https://api.openverse.org/v1/auth_tokens/register/' -ContentType 'application/x-www-form-urlencoded' -Body $datos -ErrorAction Stop
$env:OPENVERSE_CLIENT_ID = $app.client_id
$env:OPENVERSE_CLIENT_SECRET = $app.client_secret
```

Las variables de ese ejemplo duran la sesión de PowerShell. Para ejecuciones posteriores, configura ambas variables en el entorno que inicia el editor usando tu gestor de secretos. El editor obtiene un token con `client_credentials`, lo reutiliza mientras es válido y solo lo envía al catálogo. Los proveedores reciben solicitudes de descarga independientes.

```powershell
python herramientas/audio_video.py openverse bajar --papel clic "camera shutter" --max-dur 3 --n 1
python herramientas/audio_video.py openverse lista --papel clic
```

Una descarga verificada tiene un archivo de audio legible y una entrada con autor y licencia en `openverse/manifiesto.json`. Si Openverse devuelve `429`, respeta el tiempo de `Retry-After` cuando esté disponible. Si el catálogo responde y el proveedor devuelve un error al servir el archivo, el diagnóstico identifica esa segunda etapa.

### Descargar desde una ficha de Wikimedia Commons

Mientras se revisa el acceso a Openverse, el editor puede importar un efecto directamente desde Wikimedia Commons usando el título de su ficha. El comando comprueba la licencia, la huella del archivo, el tamaño y que FFprobe reconozca una pista de audio. Guarda el original con su ficha de atribución en `grabaciones/commons/`. [Grabación de obturador de ejemplo](https://commons.wikimedia.org/wiki/File:Holga_shuttersound.ogg)

```powershell
python herramientas/audio_video.py commons "File:Holga shuttersound.ogg"
python herramientas/audio_video.py real-sfx build_index
```

## Reproducir la instalación

La skill del ZIP vive en `skills/diseno-sonido/`. Copia esa carpeta al directorio de skills de Codex. El instalador de skills de Codex admite estas fuentes fijadas:

| Repositorio | Revisión | Directorios |
| --- | --- | --- |
| [Clipwing/skills](https://github.com/Clipwing/skills/tree/edbefcbc3474869e6cc1e8a7ca583b0efd0dab7e/skills/real-sfx) | `edbefcbc3474869e6cc1e8a7ca583b0efd0dab7e` | `skills/real-sfx` |
| [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/7a7f7c5c70d4a763a1eca4b3666af7c77e313f97) | `7a7f7c5c70d4a763a1eca4b3666af7c77e313f97` | `skills/earshot`, `skills/real-sound` |

Para instalar el motor en otro equipo Windows con Python 3.12, Git y FFmpeg:

```powershell
python -m venv .local/sonido/venv
.local/sonido/venv/Scripts/python.exe -m pip install "earshot[measure] @ git+https://github.com/Leonxlnx/earshot.git@7a7f7c5c70d4a763a1eca4b3666af7c77e313f97" "pillow>=10"
```

El lanzador busca `ffmpeg` y `ffprobe` en `.local/` y en el PATH. El motor básico de Earshot crea efectos en CPU. Sus módulos opcionales de escucha con modelos tienen dependencias adicionales. El cliente de [Openverse](https://api.openverse.org/v1/) requiere acceso a Internet.
