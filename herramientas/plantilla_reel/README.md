# Plantilla de edición para un reel vertical

El editor recibe un guion de voz aprobado, la locución de ElevenLabs y una orden de montaje que el director valida después de escucharla. El motor alinea palabras con Whisper, prepara los planos y exporta un MP4 de 1080 × 1920 a 30 fps. La carpeta `pistas` conserva la imagen muda y limpia, la voz, el ambiente y el SRT para editar o conformar en invideo.

## Instalar en otra PC

Conserva la plantilla dentro del repositorio. Importa de `herramientas/` la validación de órdenes y la entrega atómica de archivos. La estación de prueba ejecutó Python 3.12, Node 22, FFmpeg 9 con libx264 y Chrome. Instala también un modelo de Whisper compatible en disco, por ejemplo `base.pt`. Ejecuta estos comandos desde la raíz del repositorio.

```console
python -m venv .venv-reel
```

En PowerShell, activa ese entorno con `.\.venv-reel\Scripts\Activate.ps1`. En macOS/Linux, usa `source .venv-reel/bin/activate`.

```console
python -m pip install -r herramientas/plantilla_reel/requirements-whisper.txt
cd herramientas/plantilla_reel
npm ci
cd ../..
python herramientas/plantilla_reel/motor.py --help
python herramientas/plantilla_reel/prueba_motor.py --render
```

La prueba genera una campaña temporal con un patrón de color, un logotipo de prueba y señales de sonido. Valida una orden correcta, rechaza un hueco entre dos tomas y renderiza las variantes con y sin subtítulos. Los materiales de prueba se crean por código y se eliminan al terminar. Para una instalación con Torch CPU usa el índice oficial que corresponda a tu plataforma. Si Chrome está instalado en otra ubicación, define `MARKETING_BROWSER` con la ubicación del ejecutable. `--ffmpeg` acepta la ruta de FFmpeg. El render usa dos procesos de forma predeterminada. En una PC con poca memoria puedes fijar `REEL_CONCURRENCIA=1`.

## 1. Fijar el guion y la voz

Usa el directorio de campaña que crea el sistema. Cada producción tiene una revisión numérica. El ejemplo usa la revisión 1.

```text
campana/
  guion/voz-reel-01.json
  edicion-01/fuentes/narracion.mp3
  edicion-01/recursos.json
  Videos del proyecto - Reel de Instagram/
    01 - Videos crudos/
    02 - Referencias/
    03 - Videos terminados/
```

Cada frase lleva un identificador, el texto literal y lo que necesita mostrar la imagen. Puedes repartir una frase larga en varios cues con la clave `subtitulos`, una lista de fragmentos que juntos deben reproducir su texto.

```json
{"frases": [{"id": "f1", "texto": "Mira cómo cambia la forma.", "objetivo_visual": "Mostrar el instante del cambio."}]}
```

Genera el texto aprobado en ElevenLabs con la voz de la cuenta y conserva el audio original. Un registro local de procedencia puede contener el proveedor, el identificador de generación y la huella. Entrega el audio al motor con una ruta relativa a la campaña. El modelo se carga desde disco.

```console
python herramientas/plantilla_reel/motor.py voz campana --revision 1 --original edicion-01/fuentes/narracion.mp3 --modelo modelos/base.pt
```

El comando crea `edicion-01/pistas/voz.wav`, `edicion-01/subtitulos.srt`, otra copia del SRT junto a las pistas, el reconocimiento original en `fuentes/whisper-verificacion.json` y `alineacion.json`. Este último contiene el reloj de 30 fps, ambos SHA-256 y la procedencia de cada marca. Revisa las palabras interpoladas entre anclas. La pista reserva 100 ms antes de hablar y dos segundos para el cierre.

## 2. Seleccionar y validar los planos

Después de escuchar A1, el director y el guionista escogen los tramos de los vídeos y redactan `guion/montaje-reel-01.json` según el contrato de `campana.py validar-orden`. La duración debe cubrir exactamente los fotogramas de `alineacion.json`. En `guion_voz` se incorporan los SHA de guion y voz, las rutas de la pista y el SRT, y una lista de tomas. Cada toma indica `frase`, `archivo`, `desde` y `hasta` de la fuente, `entrada` y `salida` del reel y un `motivo` observable. Todos los tiempos se expresan en segundos. Dos tomas pueden acompañar la misma frase.

La orden también asigna las siete herramientas a sus tramos con `id`, `herramienta`, `entrada`, `salida`, `instruccion`, `insumo` y `resultado`. El guionista adapta las instrucciones a la pieza. El ejemplo íntegro de código en `prueba_motor.py` construye este contrato usando las huellas de los materiales que acaba de generar.

| Campo de una toma | Efecto en el render |
| --- | --- |
| `archivo` de un vídeo convencional | Corta el intervalo local, ajusta la velocidad a la duración asignada y llena el encuadre vertical. |
| `tratamiento: "hyperframes"` | Crea un proyecto editable por cada inserto. Dos capas de cámara con GSAP y una máscara procedente del collage guían la mirada sobre la toma. |
| `tratamiento: "placa"` | Usa la imagen de marca indicada en `archivo`, centrada sobre blanco y con su proporción original. |
| `fundido` | Duración opcional de la transición en fotogramas. |
| `reencuadre` | Filtro FFmpeg opcional definido por el editor, por ejemplo para elegir un recorte de cámara. |

Si se utiliza la animación de tinta, añade a la raíz de la orden `acento_tinta` con `frame`, `x`, `y`, `ancho`, `alto`, `opacidad` y `giro`. Su secuencia de 24 PNG RGBA se monta en esa posición. Las coordenadas consideran un lienzo de 1080 × 1920.

## 3. Configurar los recursos propios

Guarda esta configuración en `edicion-01/recursos.json`. Las rutas de los insumos se resuelven desde el directorio de campaña.

```json
{
  "ambiente": "Videos del proyecto - Reel de Instagram/01 - Videos crudos/ambiente.wav",
  "ambiente_db": -5,
  "voz_db": 0,
  "papel": "Videos del proyecto - Reel de Instagram/01 - Videos crudos/collage.mp4",
  "papel_desde": 0.5,
  "tinta": "edicion-01/fuentes/tinta"
}
```

El ambiente es un registro con permiso para el uso previsto. El motor le añade un pulso musical suave generado localmente. `voz_db` controla la ganancia de A1 en la mezcla final. El WAV conserva la ganancia de origen para poder mezclar en invideo. Cuando la orden pide un inserto HyperFrames, entrega un clip animado de gbro-collage-broll con al menos 24 fotogramas desde `papel_desde`. Para el acento, exporta de ClaudeAnimationBase `s00.png` hasta `s23.png` en la carpeta de tinta. El director también puede montar un collage completo como toma de vídeo.

## 4. Renderizar y revisar

```console
python herramientas/plantilla_reel/motor.py validar campana --revision 1
python herramientas/plantilla_reel/motor.py render campana --revision 1
```

Los insertos quedan en `edicion-01/fuentes/hyperframes-NN/`, donde NN identifica el plano. Cada carpeta contiene `index.html`, el clip de cámara, GSAP, las máscaras de papel y `inserto.mp4`. Puedes abrir esa carpeta en HyperFrames o ejecutar la comprobación de su CLI oficial. La implementación en `Reel.jsx` conserva subtítulos blancos sombreados a través de los cambios de cámara.

El máster de publicación se guarda en `03 - Videos terminados/01 - Reel.mp4`. Para una comprobación adicional puedes dar al comando una ruta libre con `--salida`. Cuando la imagen y el audio decodifican correctamente, el motor entrega las pistas y escribe sus huellas en `edicion-01/entrega-local.json`. Un bloqueo por revisión permite que varios agentes trabajen en piezas distintas sin competir por los mismos archivos.

El director monta `imagen.mp4` en V1, `voz.wav` en A1, `ambiente.wav` en A2 y `subtitulos.srt` como texto editable. Reproduce el máster y coteja los planos con las frases y con la marca. Registra el recibo del proyecto remoto y el dictamen sobre la huella exacta cuando se hayan verificado.
