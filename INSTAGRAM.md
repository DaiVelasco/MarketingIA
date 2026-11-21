# Instagram para el equipo de marketing

El director usa los datos de Instagram para decidir qué probar. Investigación observa el rendimiento, Analítica describe el patrón y Contenidos lo convierte en una pieza original. Publicación conserva el recibo de Meta. Comunidad consulta los comentarios de los reels y carruseles propios mientras el estudio prepara la campaña siguiente.

## Conectar la cuenta una vez

1. Vincula la cuenta profesional de Instagram de la marca a su página de Facebook. Un administrador de esos activos configura la app con **Instagram API con Facebook Login for Business**. Selecciona en el panel la versión Graph habilitada para la app. Si Meta exige revisión de permisos, nivel de acceso avanzado o autorización de publicación de la página, completa el trámite aplicable a esa cuenta. [Inicio oficial de Meta](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login/get-started)
2. Completa el login de negocio. Para descubrir la página, solicita `pages_show_list`. Para esta integración revisa `instagram_basic`, `pages_read_engagement`, `instagram_manage_insights`, `instagram_content_publish` e `instagram_manage_comments`. Los activos asignados vía Business Manager pueden requerir permisos adicionales. En el explorador oficial y con el token de usuario, consulta `GET /me/accounts?fields=id,name,instagram_business_account,access_token`. Selecciona la página de la marca y extrae su token de página y el ID de `instagram_business_account`. Guarda los valores en el gestor de credenciales del equipo. [Conectar los activos](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login/get-started) · [Descubrimiento de cuentas](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery)
3. Expón las variables siguientes al **proceso que ejecuta Codex**. En Windows, los cambios en las variables del usuario se heredan tras cerrar y volver a abrir la aplicación. Configura las credenciales desde tu equipo y conserva su fecha de expiración fuera del ZIP.

| Variable | Valor |
| --- | --- |
| `MARKETINGIA_IG_ID` | ID numérico de la cuenta profesional de Instagram |
| `MARKETINGIA_GRAPH_VERSION` | Versión de Graph que muestra tu app, con formato `vNN.N` |
| `MARKETINGIA_PAGE_TOKEN` | Token de la página vinculada, para identificar la cuenta, consultar sus medios y publicar |
| `MARKETINGIA_DISCOVERY_TOKEN` | Token de usuario de Facebook autorizado para Business Discovery, Insights y comentarios |
| `MARKETINGIA_MEDIA_OUTBOX` | Opcional. Ruta local o montada de la carpeta de la marca que sirve los JPG públicamente o los sincroniza con el alojamiento |

Desde la raíz ejecuta estas lecturas en modo ensayo. El diagnóstico revela presencia de variables. La consulta de cuenta comprueba el ID y el nombre devueltos por Meta frente a la configuración. En `operacion.toml`, escribe en `referencias` las cuentas profesionales elegidas, sin arroba. Empieza con personas o negocios que hablen a un público relevante.

```powershell
python instagram.py diagnostico
python instagram.py cuenta
python instagram.py propios --formato todos
python radar.py capturar
python radar.py clasificar
```

El radar externo puede recibir recuentos públicos de reproducciones mediante Business Discovery. Conserva el valor ausente si Meta lo omite. Para la cuenta propia utiliza Insights. Cuando falten credenciales, los archivos de referencia, exportaciones propias y el brief permiten producir un ensayo. `python radar.py demo` usa cifras ficticias para verificar el cálculo. [Business Discovery de Meta](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery)

## Qué aporta instagram-agent-skill

El proyecto incluye las trece skills originales en `referencias/instagram-agent/skills/` y su licencia. Un agente puede leer directamente el `SKILL.md` que necesita en otra PC. El adaptador `instagram.py` aporta el acceso autenticado. Cada campaña utiliza la voz y las fuentes de su propia marca. [Repositorio de referencia](https://github.com/Jakeschincariol/instagram-agent-skill)

| Quién la usa | Skills | Decisión que recibe el siguiente agente |
| --- | --- | --- |
| Investigación y Analítica | `ig-viral`, `ig-audit`, `ig-profile` | Reel destacado y reel típico de la misma cuenta, señales de alcance, evidencia observable y una hipótesis |
| Director y Contenidos | `ig-plan`, `ig-repurpose` | Objetivo, formatos y una pregunta propia de la marca para cada pieza |
| Contenidos, Editor y Diseño | `ig-reel`, `ig-carousel`, `ig-story` | Tres aperturas candidatas, una secuencia con tiempos, cuatro láminas y dos historias según el encargo |
| Contenidos y Revisión | `ig-caption`, `ig-human` | Primera línea legible, voz natural, un CTA y texto revisado en español |
| Comunidad y Conversión | `ig-reply`, `ig-comment`, `ig-dm` | Clasificación, borradores de respuesta y seguimiento. La operación automática de esta integración atiende comentarios públicos en medios propios |

Los scripts de la referencia sirven de apoyo. Para un reel, `beats.py guion.txt --target 30` estima tiempos a partir de palabras y `hookscore.py aperturas.txt` compara candidatas. Ambos están en `referencias/instagram-agent/skills/ig-reel/`. Parte de sus reglas lingüísticas están escritas para inglés. Contrasta el resultado con una lectura en voz alta en español y ajusta la escaleta a la duración de la pista definitiva.

## Pasar de ensayo a operación diaria

La campaña completa produce el reel y el conjunto gráfico. El director elige una pieza de feed por día de Caracas. El resto queda disponible para otro día. Las dos historias se entregan como JPG. Comprueba la oferta vigente, el destino del CTA y el FAQ en MARCA.md. Tras configurar Meta y autorizar el funcionamiento recurrente en la cuenta, usa `modo = "produccion"` y habilita únicamente las acciones del alcance elegido. Para reels, carruseles y respuestas públicas el valor es `acciones_habilitadas = ["publicar", "publicar-carrusel", "responder"]`. El valor `ensayo` permite reproducir la cadena editorial y consultar datos con acceso válido.

**Reel.** En la carpeta del día, Revisión reproduce el MP4, escucha la mezcla y comprueba el texto. La ficha de huellas comienza con `aprobado` en `false`. Cuando el responsable verifica la pieza, cambia ese campo a `true` en la ficha correspondiente. La aprobación editorial la puede dar el propio agente de Revisión dentro del encargo recurrente. El siguiente ejemplo de PowerShell se ejecuta desde la raíz del proyecto con la fecha de la campaña. El ejemplo obtiene el día local según la zona configurada.

```powershell
$dia = python -c "from campana import cfg,local_day; print(local_day(cfg()['zona']))"
$cuenta = python -c "from campana import cfg; print(cfg()['cuenta'])"
$base = "campanas/$cuenta/$dia"
$revision = 4  # Sustituye por la revisión aprobada del día
$numero = '{0:D2}' -f $revision
$mp4 = "$base/Videos del proyecto - Reel de Instagram/03 - Videos terminados/$numero - Reel.mp4"
$pie = "$base/guion/pie-de-foto.txt"
$qa = "$base/revision/qa-reel-$numero.json"
python campana.py huellas reel "$mp4" "$pie" --fecha $dia --salida "$qa"
```

Una vez aprobada esa ficha, el agente ejecuta `python instagram.py publicar $dia "$mp4" "$pie" "$qa"`. El adaptador verifica cuenta, día, formato y huellas. Abre un contenedor, carga el MP4 y espera a que Meta complete el procesamiento. El resultado `confirmado` contiene el ID publicado. [Publicación de contenidos en Meta](https://developers.facebook.com/documentation/instagram-platform/content-publishing)

**Carrusel.** Los cuatro JPG pertenecen a `entrega/publicar/carrusel/`, en orden `01.jpg` a `04.jpg`. El pie de foto viaja en la misma entrega. Revisión abre las láminas, verifica el orden, legibilidad y fotos, y compara con el ZIP exportado.

```powershell
$entrega = "$base/carrusel/entrega"
$qa = "$base/revision/qa-carrusel-01.json"
node herramientas/exportar.cjs "$base/carrusel" --verificar
python campana.py huellas carrusel "$entrega" --fecha $dia --salida "$qa"
```

Configura `base_imagenes_https` en `operacion.toml` con el directorio público del alojamiento. Los archivos se sirven como `<sha256>.jpg` y deben ser legibles por Meta sin inicio de sesión. Para automatizar este paso, vincula `MARKETINGIA_MEDIA_OUTBOX` al directorio existente que publica o sincroniza esos archivos. El adaptador deposita los cuatro JPG aprobados allí y comprueba que cada URL devuelve exactamente esos bytes. También se pueden preparar en el alojamiento por otro medio. Un servidor que recomprime JPEG requiere una ruta que sirva los originales. [Requisitos de medios públicos](https://developers.facebook.com/documentation/instagram-platform/content-publishing)

Con la ficha aprobada, Publicación ejecuta `python instagram.py publicar-carrusel $dia "$entrega" "$qa"`. Meta crea un contenedor por lámina. El adaptador conserva su posición y usa esos cuatro IDs para crear el álbum. En una revisión posterior cambia el número de entrega y de ficha según corresponda.

## Comunidad y aprendizaje

Comunidad obtiene los IDs con `python instagram.py propios --formato todos`. Consulta un hilo con `python instagram.py comentarios ID_MEDIO`. En ensayo guarda los textos candidatos en el proyecto. En producción responde con `python instagram.py responder ID_MEDIO ID_COMENTARIO ARCHIVO_TEXTO`. El adaptador comprueba propiedad, autor, visibilidad del comentario y respuestas anteriores de la marca. Los reclamos, cobros, datos personales y preguntas sin fuente vigente se derivan al responsable de atención. Los DM, los comentarios en perfiles de terceros y las interacciones de historias quedan a cargo del equipo humano. [Comentarios de Meta](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-media/comments) · [Respuestas públicas](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-comment/replies)

Analítica ejecuta `python instagram.py metricas ID_MEDIO` a las 24 h, 72 h y 7 días. Registra hora efectiva, formato, alcance, vistas, guardados y compartidos cuando aparezcan. Si se pierde una ventana, guarda la antigüedad real. Para crecimiento compara compartidos por cada 1.000 cuentas alcanzadas entre piezas comparables. Para reservas y ventas cuenta hilos con intención explícita. El sistema interno de la marca conserva las conversiones finales. Una campaña que invite a escribir «INFO» por DM precisa un conteo agregado de la bandeja para evaluar ese objetivo.

## Recuperar una ejecución

| Situación | Acción del director |
| --- | --- |
| `procesando` | Espera aproximadamente un minuto y repite el comando original con la misma ficha. Si persiste tras cinco consultas, deja el ID pendiente y vuelve más tarde dentro de la jornada. |
| `confirmado` o `ya_atendido` | Conserva el ID de medio o respuesta. Al repetir el encargo se recupera el recibo. |
| `cargando` | Repite el mismo comando para consultar el contenedor guardado. Si Meta devuelve `FINISHED`, el adaptador retoma la entrega. Si la carga sigue incierta, conserva el ID para conciliación. |
| `enviando`, tiempo de espera agotado o estado remoto `PUBLISHED` sin recibo | Consulta `python instagram.py registro`, el contenedor y los medios o respuestas recientes de la cuenta. Anota el ID público verificado en la campaña. El director mantiene esa clave ocupada para prevenir un duplicado. |
| Contenedor en error o caducado, JPG remoto distinto, alcance revocado | Anota la causa, repara el alojamiento o acceso y comprueba el estado remoto. Un envío terminal queda como incidencia de esa jornada. |
| Reinicio o traslado a otra PC | Pausa el ejecutor anterior, cierra sus procesos y copia `estado/` junto con las campañas. Ejecuta un solo publicador para cada cuenta. Los registros guardan una clave de feed por cuenta y día, y otra por comentario. |

Desde la raíz, `python -B -m unittest discover -s pruebas` reproduce los controles de envío y recuperación con una cuenta ficticia. La validación en la cuenta de la marca requiere sus credenciales y permisos activos.

