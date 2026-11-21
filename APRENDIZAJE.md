# Memoria editorial por cuenta

El director y la skill portable leen `memoria/<cuenta>/MEMORIA.md` antes de proponer variantes. `aprendizaje.sqlite`, en la misma carpeta, conserva el historial confirmado. Al cambiar de PC, copiar esa carpeta con MarketingIA cuando las escrituras hayan terminado. Python 3.11 o posterior es suficiente para leer o registrar datos locales.

## Del portal al siguiente brief

1. El portal entrega la elección del administrador con las opciones exactas que vio, el formato de cada una y sus rasgos observables. Si el administrador explica el porqué, se conserva su texto. La ausencia de explicación queda registrada. Desde la primera selección, el Markdown muestra hasta tres alternativas con sus diferencias y rasgos comunes. Una pregunta para la ronda siguiente propone variar un solo rasgo respetando las instrucciones vigentes. El resumen JSON conserva todas las opciones.
2. El director registra por separado las instrucciones que el usuario da expresamente, con el chat u otra fuente verificable. Estas directrices tienen vigencia hasta una corrección o retirada.
3. El lector de Instagram comprueba la identidad con el adaptador existente y registra mediciones de publicaciones propias. La elección de una propuesta, la publicación real y la evidencia de rendimiento son tres hechos independientes.
4. Los agentes pueden proponer una prueba basada en las tendencias del administrador y contrastarla con resultados publicados. El texto de cada sección indica su origen. Si el administrador elige algo que baja en Instagram, el director conserva ambos hechos y diseña la siguiente prueba cambiando un solo rasgo.

## Comandos

Ejecutar desde la raíz del proyecto. `--raiz` permite usar una copia o un directorio temporal. `--cuenta` acepta la cuenta de trabajo. Si se omite, se lee la cuenta de `operacion.toml`.

```powershell
python -B aprendizaje.py --cuenta cuenta.demo resumen
python -B aprendizaje.py --cuenta cuenta.demo registrar evento.json
python -B aprendizaje.py --cuenta cuenta.demo historial decision jornada-01
python -B aprendizaje.py --cuenta cuenta.demo importar-radar
python -B aprendizaje.py --cuenta cuenta.demo sincronizar --limite 30
```

`registrar` admite un objeto o una lista JSON en UTF-8 y también `-` para leer stdin. Un lote inválido se revierte completo. La interfaz Python es `herramientas.aprendizaje.registrar(raiz, cuenta, evento)` y `resumen(raiz, cuenta)`. El primero devuelve tipo, id, revisión y si hubo un cambio. El segundo actualiza el Markdown y devuelve el detalle completo como diccionario. Para listas de eventos usar `registrar_lote`. Las operaciones remotas de sincronización son lecturas. La memoria carece de operaciones de publicación o respuesta.

| Tipo | Campos | Uso |
| --- | --- | --- |
| `instruccion` | `id, directriz, fuente`, opcionales `formato, fecha` | Petición explícita del usuario. El alcance es todos los formatos salvo indicación. |
| `decision` | `id, formato, elegida, opciones[]`, opcionales `motivo_admin, fecha` | ID estable de la ronda y ID exacto de la opción seleccionada. Cada opción lleva `id`, `formato`, `titulo` y la lista `rasgos`. El formato de la decisión es el elegido. Un formato de opción omitido hereda el de la decisión. |
| `vinculo` | `id, decision, candidata` | ID numérico real de Instagram junto a la elección efectivamente publicada. Congela la revisión y los rasgos de la opción elegida. |
| `etiquetas` | `id, formato, rasgos, fuente` | Rasgos que alguien verificó directamente en el contenido de un ID de Instagram, incluso si precede al portal. Estos datos pueden corregir el etiquetado de la propuesta después de ver la pieza final. |
| `muestra` | `medio, formato, publicado, observado, metricas, fuente`, opcional `enlace` | Una lectura con fechas ISO 8601 con zona. Su id se forma con medio y fecha/hora UTC de observación. Las métricas admitidas son vistas, me_gusta, comentarios, guardados, alcance y compartidos. Omitir las que falten o enviar null. |
| `retirar` | `clase, id, motivo` | Retira de la proyección una versión incorrecta o caducada. El historial conserva la decisión y el motivo del retiro. |

Una actualización con el mismo tipo e ID crea una revisión. La repetición del mismo contenido devuelve el recibo anterior. Para una corrección concurrente, enviar también `si_revision` con la versión que se leyó. El administrador puede corregir el motivo modificando la decisión completa. Una retirada del vínculo afecta a la atribución de rasgos del post. Una corrección posterior en la tarjeta del portal conserva la versión vinculada como registro de la pieza que realmente se publicó. Los errores de vinculación se corrigen directamente en `vinculo` o `etiquetas`.

## Conexión con los registros existentes

`sincronizar` usa `instagram.Meta.identity`, la colección paginada de medios propios y los conteos de me gusta y comentarios. Solicita vistas, alcance, guardados y compartidos en Insights. Si falla el conjunto por permisos de una métrica, intenta recuperar los contadores compatibles. Devuelve los errores de captura en `avisos`. Con `--solo-publicas` recoge únicamente los conteos disponibles en la colección de medios. Lee las páginas de Meta por demanda, con un máximo de 50 filas por petición. Se detiene al reunir el número de medios compatibles indicado por `--limite` o al revisar 500 medios de la colección en el orden que entrega Meta. Permite importar capturas antiguas tomadas en el momento adecuado.

El registro local `estado/acciones.sqlite` puede enlazar una publicación confirmada cuando la cuenta, el ID remoto, el formato y la huella del contenido coinciden con una sola opción elegida. La opción tiene que incluir `huella_publicacion`, una cadena idéntica a la que calcula el adaptador a partir del máster o los JPG y del caption. Una publicación histórica con fecha parecida y otra imagen permanece sin atribución. `importar-radar` puede incorporar las vistas anteriores desde `estado/radar.sqlite` para la cuenta seleccionada. Conserva muestras previas más completas y las retiradas.

## Cómo se calculan las tendencias

**Elección editorial.** Durante 90 días se cuentan rondas distintas donde se podía elegir más de una opción del mismo formato y todas esas opciones tenían rasgos descritos. Un rasgo común a todas carece de contraste. Una pista entra en el resumen cuando hay al menos tres elecciones a favor o tres omisiones, y la proporción elegida difiere al menos 20 puntos porcentuales de la presencia media del rasgo en las alternativas. En rondas mixtas, una comparación de gustos sobre un rasgo solo usa las opciones del formato ganador. Las elecciones entre formatos quedan disponibles como datos explícitos. La inferencia caduca al salir las rondas de la ventana.

**Respuesta de la audiencia.** Comparar publicaciones de la misma cuenta y formato a edades equivalentes. Se usan 18–30 h para el corte de 24 h, 60–84 h para el de 72 h y 144–192 h para el de siete días. Para cada publicación y corte se elige la lectura más próxima a la edad objetivo. Un empate favorece la más completa. Las capturas fuera de ventana todavía figuran en el historial y en los conteos disponibles.

Para cada métrica se toman hasta doce publicaciones anteriores con datos en el mismo corte y dentro de los 180 días previos. Se necesitan cinco publicaciones distintas como mínimo. Las vistas se comparan por conteo. Los me gusta, comentarios y guardados se comparan por mil cuentas alcanzadas si el alcance del post es de al menos 30. En ese caso, las referencias también deben tener alcance de al menos 30. Cuando no hay cobertura para calcular la tasa del post, se usa el conteo y se identifica esa unidad. Una referencia válida requiere una mediana de al menos 20 vistas o dos interacciones según la métrica. Un valor observado de cero se conserva. Un dato ausente sigue ausente.

El índice es la media geométrica de los múltiplos sobre cada mediana. Vistas pesa 45 %, me gusta 20 %, comentarios 15 % y guardados 20 %. Los compartidos se conservan como conteo para contrastar objetivos como crecimiento. Cada contribución al índice se acota entre 0,25× y 4× para limitar el efecto de atípicos. Se renormalizan los pesos disponibles solo si hay al menos dos métricas con base y un 45 % de peso original. Un índice desde 1,25× se considera alto y hasta 0,80× se considera bajo. Un post sin base suficiente conserva sus cifras en el registro.

**Hipótesis por rasgo.** Se exige que al menos tres publicaciones distintas estén etiquetadas con el rasgo y tengan índices comparables en el mismo formato y corte. Al menos dos tercios deben ir en la misma dirección y la mediana debe cruzar el umbral. Cada post participa una vez, prefiriendo 72 h, luego siete días y luego 24 h. Se consideran las publicaciones de los últimos 180 días. Las cifras describen asociación y sirven para elegir una prueba. Los posts sin etiquetas contribuyen a la base de su formato sin atribuirles una técnica creativa desconocida.

**Reproducción y pruebas.** SQLite serializa la operación de cada cuenta. Cada evento y su corrección se confirman en una transacción, y el Markdown se reemplaza de forma atómica mientras se retiene el bloqueo de materialización. Ante una interrupción, ejecutar `resumen` lo reconstruye desde SQLite. El historial almacena todas las versiones. La vista Markdown resume las doce elecciones y lecturas más recientes, mientras que el resumen JSON ofrece la lista completa. Las pruebas con datos sintéticos se ejecutan en carpetas temporales con `python -B -m unittest discover -s pruebas -p test_aprendizaje.py`.
