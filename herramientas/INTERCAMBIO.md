# Intercambio de propuestas con el portal del administrador

El equipo prepara un ZIP por ronda con el reel completo, las cuatro láminas en orden de cada carrusel y sus pies de foto. Una jornada puede tener varias rondas. El portal de la otra máquina presenta las opciones al administrador y devuelve su elección a MarketingIA como un JSON.

## Preparar la carpeta de la campaña

Ejecuta `python -m unittest discover -s pruebas -p test_portal.py` para probar una ronda, la importación de una selección y el aislamiento de varias rondas con archivos sintéticos temporales.

En `portal/catalogo.json`, Dirección indica la cuenta, la jornada, un identificador estable y las piezas concretas que revisó el equipo. Cada opción tiene un id único, formato, versión, título, rasgos visuales y narrativos, archivos en orden, caption y dictamen editorial. Las rutas de las tres últimas entradas se expresan respecto de la campaña y van acompañadas del SHA-256 registrado al revisar el archivo. Por ejemplo, esta es una opción de reel dentro del catálogo. Completa el mismo conjunto con otra opción de reel o un carrusel con los cuatro JPG numerados.

```json
{
  "cuenta": "cuenta.demo",
  "jornada": "2026-11-21",
  "id": "2026-11-21/feed",
  "opciones": [{
    "id": "reel-01",
    "formato": "reel",
    "version": 1,
    "titulo": "Cómo se realiza el acabado",
    "rasgos": ["Pregunta narrada", "Vista general y detalle del resultado"],
    "archivos": [{"archivo": "Videos del proyecto - Reel de Instagram/03 - Videos terminados/01 - Reel.mp4", "sha256": "<huella del MP4 revisado>"}],
    "caption": {"archivo": "guion/pie-de-foto.txt", "sha256": "<huella del caption>"},
    "revision_editorial": {"archivo": "revision/reproduccion-reel-01.md", "sha256": "<huella del dictamen>"}
  }]
}
```

```powershell
python -B portal.py preparar campanas/cuenta.demo/2026-11-21
```

El comando escribe `portal/propuestas.zip` e imprime su SHA-256. El resultado es reproducible con las mismas entradas. Revisa un archivo modificado y actualiza su entrada del catálogo antes de crear otro paquete.

## Abrir otra ronda el mismo día

Asigna un identificador propio al nuevo conjunto. Para la segunda ronda del 21 de noviembre, el identificador es `2026-11-21/segundo-conjunto` y su catálogo vive en `portal/ronda-02/catalogo.json`. Las rutas de medios, pies de foto y dictámenes siguen siendo relativas a la carpeta de la campaña. El argumento `--ronda` es el nombre de la subcarpeta dentro de `portal/`.

```powershell
python -B portal.py preparar campanas/cuenta.demo/2026-11-21 --ronda ronda-02
```

Entrega `portal/ronda-02/propuestas.zip` al administrador cuando su portal esté disponible. Cuando devuelva su elección, guarda el JSON recibido y ejecuta el comando de la misma ronda.

```powershell
python -B portal.py importar campanas/cuenta.demo/2026-11-21 decision-ronda-02.json --ronda ronda-02
```

La segunda elección queda en `portal/ronda-02/seleccion.json`. Cada ronda tiene sus propias revisiones y su historial de decisión en la memoria. Para trabajar con la primera ronda usa los comandos originales sin la opción `--ronda`.

## Leer el paquete en el portal

El punto de entrada del ZIP es `manifiesto.json`. Contiene `version` (1), `id`, `cuenta`, `jornada` y `opciones`. Por cada opción, presenta el título, el formato y su versión. En `archivos`, cada elemento contiene la ruta **dentro del ZIP** y su SHA-256. El orden de los elementos corresponde al orden de las láminas. Para un reel hay un MP4. El campo `caption` apunta al pie de foto UTF-8. El portal puede comprobar las huellas antes de ofrecer la vista previa. El ZIP no incluye credenciales ni recursos de trabajo como voces o archivos crudos. La transferencia y la autenticación del administrador se configuran en el portal cuando se conozca el entorno remoto.

## Devolver la elección

Guardar un JSON con esta estructura. La revisión 1 es la primera elección del grupo. Una corrección conserva el id, usa la próxima revisión y registra el instante de esa decisión con su zona horaria.

```json
{
  "cuenta": "cuenta.demo",
  "id": "2026-11-21/feed",
  "paquete_sha256": "<SHA-256 de los bytes del ZIP recibido>",
  "revision": 1,
  "fecha": "2026-11-21T18:30:00-04:00",
  "elegida": "carrusel-02",
  "motivo_admin": "Texto opcional escrito por el administrador"
}
```

```powershell
python -B portal.py importar campanas/cuenta.demo/2026-11-21 decision.json
```

La importación verifica el ZIP, sus entradas y las fuentes locales. Recupera del catálogo la descripción, el formato y las huellas que corresponden al id elegido. Un reintento del mismo JSON produce el mismo resultado. Una revisión tardía o una elección sobre archivos distintos se rechazan.

El recibo en `portal/seleccion.json` guarda cuenta y jornada, id de conjunto, fecha y revisión de la decisión, versión de la pieza, formato, id elegido, motivo literal, huella del ZIP, medios y caption (rutas locales relativas y SHA-256), y la huella conjunta de publicación. El módulo de aprendizaje registra las opciones ofrecidas y la elección en la memoria de esa cuenta. La preferencia sirve para el aprendizaje editorial. La publicación conserva el flujo de permisos y revisión del proyecto.
