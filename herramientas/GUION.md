# Guion de rodaje de Konduce

El filmmaker debe poder llegar mañana al taller, leer una escena y saber dónde poner el teléfono, qué pedirle a la persona y cuándo tiene la toma. Quien edita debe poder encontrar el corte viendo o escuchando esa misma acción.

## Antes de escribir

1. **Dirección** identifica la fecha y el turno del calendario en el brief. Ejecuta `python campana.py historial-guiones CARPETA` y lee los títulos, primeras frases y primeras imágenes de las últimas siete jornadas disponibles, incluidos los turnos ya preparados para hoy. Revisa el guion anterior si su ficha histórica carece de motivo o forma. Anota en el brief qué podría repetirse y qué cambia esta vez. Las tres aperturas candidatas son apuntes internos; se desarrolla y entrega **una sola historia por turno**. Una corrección conserva el turno y recibe una nueva revisión.
2. **Investigación** contrasta los datos con la ficha de marca y una fuente autorizada vigente. Registra el servicio, horario, precio o beneficio exacto y la fecha o periodo que lo respalda. Si falta confirmación, escoge un detalle que se pueda demostrar con la cámara u otra historia. Un letrero antiguo y una dramatización sirven como referencia visual. La vigencia comercial la confirma la marca.
3. **Dirección y Contenidos** fijan por qué un conductor querría quedarse y qué sabrá al final. Si hay tres turnos, uno podría resolver cómo señalar una marca en un rin, otro acompañar una etapa de un lavado confirmado y el tercero seguir un intercambio real al llegar. Verifica cada situación; varía tema, primera imagen y manera de contarla. Una duda, un procedimiento y una llegada son posibilidades, no una parrilla fija.

## Escritura

Escribe en español venezolano conversado, desde el taller de Konduce en Valencia, Carabobo. Usa el tuteo y palabras que diría la persona que aparece. Lee las frases en voz alta. Deja que respiren. Abre con **algo que cambia ante la cámara**. La primera frase despierta una duda que el reel resolverá; también puede ser una afirmación. Evita repetir «¿Tu carro necesita…?» o «Vente un momento, que te muestro».

Desarrolla el cuerpo de la historia. Sitúa al conductor, muestra el detalle que suele pasar por alto, sigue la acción hasta que algo cambie y deja ver la consecuencia. Da el porqué cuando le sirva al cliente. En un procedimiento, elige el paso que explica el resultado; en una conversación, conserva la respuesta que cambia lo que hace el técnico. Si una frase podría acompañar cualquier imagen, escribe qué debe mirar u oír el espectador. Da más espacio a las historias que lo necesitan. Una historia resuelta en 17 segundos puede terminar ahí; si el brief pide 30, desarrolla una observación, una decisión o una comprobación que merezca ese tiempo.

**Ejemplo para rodaje.** El cliente, junto al carro estacionado, dice «Es aquí, cerquita de la válvula». Señala una de dos marcas visibles en el rin. El asesor sigue el gesto y pregunta «¿Esta de aquí?». El cliente asiente y dice «Esa misma». Filma la conversación desde el lado del asesor en plano medio. Para el inserto, baja el teléfono a la altura del rin y deja la válvula y el dedo enfocados. Entra cuando el cliente se agache. Corta con el asentimiento y conserva «Esa misma» sobre el primer cuadro del detalle. El espectador ve cuál de las dos marcas quisieron señalar. Usa este ejemplo cuando el detalle exista en el carro del rodaje.

## Archivo que recibe el equipo

Contenidos completa **un solo original**, `guion/voz-reel-NN.json`. Conserva `titulo` y `frases`. Cada frase lleva `id`, `texto` hablado literal y `objetivo_visual`. La posición de las frases fija el orden de CLARI y de los subtítulos. Añade un objeto `rodaje` con estos campos:

| Campo | Qué escribe Contenidos |
| --- | --- |
| `turno` | Identificador estable del espacio de ese día, acordado con Dirección. La revisión numérica identifica la versión. |
| `tema`, `motivo`, `forma` | Tema específico, razón para quedarse y manera de seguir la historia. |
| `direccion` | Una o dos frases con punto de vista, ritmo y lo que se debe ver al resolverse la historia. |
| `pregunta`, `respuesta` | Duda que despierta el arranque y hecho visible o audible que la resuelve. Orientan al equipo y solo se pronuncian si aparecen en `frases`. |
| `pie_de_foto` | Texto de publicación terminado, en la voz de la cuenta. Si lleva invitación, conserva la misma acción que pide la voz. |
| `fuentes_comerciales` | Lista de objetos con `dato`, `fuente` y `vigencia`. Usa `[]` si ninguna afirmación comercial necesita respaldo. |
| `cta_frase`, `cierre` | ID de la última frase hablada y descripción de la toma estable, el espacio para la firma y la salida sonora. Elige **un solo CTA** que tenga sentido después de ver la demostración. |
| `escenas` | Lista ordenada con los cinco bloques siguientes. |

| Bloque por escena | Qué recibe rodaje y edición |
| --- | --- |
| Locución | `frases` con los ID exactos, en orden, e `intencion` entre `cercano`, `curioso`, `sereno`, `enérgico` o `seguro`. Para un gesto que se entiende por su sonido, usa `frases: []` y describe qué se oye en `sonido`. |
| Toma | `toma.quien` identifica al sujeto, `toma.accion` lo que hace y `toma.fin` el momento en que termina. Indica si hay que filmarla, si será una ilustración Genjutsu o si se necesita material de archivo. Biblioteca localizará el archivo y sus segundos tras alinear la voz. |
| Cámara y detalles | `camara.posicion` indica desde dónde y a qué altura poner el teléfono, `camara.plano` el tamaño de plano y `camara.foco` el detalle enfocado. Grabar en vertical 9:16, con horizonte derecho y un segundo antes y después del gesto. Esos dos márgenes sirven al corte y quedan fuera de la duración estimada. |
| Edición y sonido | `edicion.entrada` identifica el gesto inicial, `edicion.corte` el cuadro o sonido de salida y `edicion.enlace` lo que veremos u oiremos a continuación. Para una transición, indica las dos imágenes y la relación entre ellas. `sonido` precisa voz limpia, entrada o bajada de música, efecto puntual o silencio. Asocia cada efecto al fotograma de la acción y deja las pausas libres del ruido del taller. Prioriza sonidos, logo y gráficos globales de Konduce. Pide Remotion o Converzzo cuando ayuden a entender algo concreto. |
| Texto y duración | `segundos` estima el tiempo en pantalla; la hoja suma los intervalos. `texto_grafico` contiene el texto exacto de un dato útil o `null` para un plano limpio. Los subtítulos siguen siendo grandes, legibles y sincronizados con la voz aunque no haya gráfico. |

Por ejemplo, si `f2` contiene «Esa misma», este fragmento especifica cómo filmar y editar su respuesta:

```json
{
  "segundos": 2.5,
  "frases": ["f2"],
  "intencion": "seguro",
  "toma": {"quien": "El cliente", "accion": "Asiente mirando el rin.", "fin": "Termina de decir «Esa misma»."},
  "camara": {"posicion": "A la altura de sus ojos, del lado del asesor.", "plano": "Primer plano", "foco": "los ojos del cliente"},
  "edicion": {"entrada": "Entra al volverse hacia el asesor.", "corte": "Corta cuando baje la barbilla.", "enlace": "Pasa al dedo junto a la válvula y deja terminar «misma» sobre la marca."},
  "sonido": "Baja la instrumental al asentir. Deja «Esa misma» en primer plano, con la voz limpia.",
  "texto_grafico": null
}
```

Reserva una toma estable, con espacio en el centro para el logo y su halo blanco suave. Sitúa ese tratamiento en la toma propia de salida y deja respirar el CTA. Incluye en los segundos del guion la transición y los últimos 78 cuadros de la placa aprobada a 30 fps. La firma de referencia conserva su imagen original. [Cierre de la cuenta](../MARCA.md#cierre-de-los-reels)

## Lectura y traspaso

**Dirección y Revisión** leen en voz alta la locución, cronometran una lectura con los gestos y comprueban que la respuesta se vea antes del CTA. Revisión señala la escena exacta si faltan posición de cámara, acción, corte, fuente o continuidad de sonido. Devuelve «mostrar confianza» o «hacer una transición dinámica» con una indicación que el filmmaker pueda ejecutar. Dirección contrasta las diferencias de fondo entre turnos incluso cuando los títulos usan palabras distintas.

**Dirección** valida con `python campana.py validar-guion CARPETA --revision N --hoja`. El comando comprueba los campos, el orden de la voz, el CTA final y las repeticiones literales entre turnos del día. Entrega `guion/rodaje-reel-NN.md` al filmmaker y a `editor_video`. La lectura editorial decide si la promesa se cumple y si las fuentes prueban lo escrito.

**Edición** recibe el encargo que el prompt llama «OpenCode». Produce la voz aprobada de CLARI, conserva las pausas de sonido previstas, alinea con Whisper y entonces selecciona el metraje con Biblioteca. Traslada los cortes propuestos al reloj real en `montaje-reel-NN.json`. Una toma hablada se vincula a `frase`. Para un gesto sin locución, usa `escena` con el número de la hoja (desde 1), omite `frase` y conserva archivo, tiempos y motivo. La toma nueva de Genjutsu tiene una función asignada en la historia. Revisión escucha y mira el máster contra la misma hoja y la placa de marca. Si el encargo es solo de guion, la entrega termina en la hoja legible.
