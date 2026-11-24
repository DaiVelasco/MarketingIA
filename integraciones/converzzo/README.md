# Edición con Converzzo

MarketingIA incluye las 57 skills de Efectos y las 31 de Tipografía como dos plugins de Codex. Dirección puede recibir «muestra cómo se mueve la herramienta» y delegar la elección de la operación. Si la toma ya explica el gesto, conserva el corte limpio. Las fichas contienen parámetros, ejemplos de capas y archivos de entrada. [Skills de Efectos](marketplace/plugins/efectos-converzzo/skills/) · [Skills de Tipografía](marketplace/plugins/tipografia-converzzo/skills/)

## Preparar una estación

Desde la raíz del proyecto, con Git, Python 3.12, uv, Node.js con npm, FFmpeg y FFprobe en PATH. Para registrar los plugins se utiliza la CLI de Codex con `codex plugin`. La prueba de ambos modelos y los renders se hicieron en Windows con CPU y Chrome. Puedes indicar otro ejecutable de Chrome o Chromium con `CONVERZZO_CHROME`.

```powershell
python herramientas/converzzo.py preparar
python herramientas/converzzo.py activar
python herramientas/converzzo.py modelos
python herramientas/converzzo.py estado
python herramientas/converzzo.py catalogo
```

`preparar` obtiene los dos motores de los commits fijados, aplica las adaptaciones de MarketingIA e instala sus dependencias en `.local/converzzo/`. `activar` registra el catálogo local y habilita ambos plugins en el perfil de Codex. `modelos` prepara PyTorch para CPU, descarga SAM 2.1 Hiera Small para seguimiento y Depth Anything V2 Small para profundidad y verifica los pesos con SHA-256. Puedes ejecutar este último paso cuando necesites esos efectos. El catálogo se consulta incluso antes de instalar los motores. [Versiones y huellas](versiones.json)

## Traspaso de una escena

El usuario delega la elección de herramientas al plantear el objetivo del video. Dirección aprueba el plan de la escena y Edición puede ejecutarlo sin pedir al usuario que elija una skill o confirme cada efecto.

| Responsable | Decisión y entrega |
| --- | --- |
| Biblioteca | Localiza el original, reproduce el tramo y devuelve segundos, encuadre y cortes. Para seguimiento, incluye el fotograma de referencia y el punto o caja normalizados sobre el encuadre final. Para paralaje, identifica qué quedará delante y detrás. |
| Dirección y Contenidos | Eligen el efecto por su función en el relato. En la orden de montaje registran `herramienta` con el nombre del plugin, `skill` con el identificador exacto de la ficha, tramo, insumo, ajuste y resultado observable. Dirección valida la orden con `campana.py validar-orden`. |
| Edición | Traduce la orden al plan JSON del motor. Si cambia la velocidad o el recorte, recalcula el instante y las coordenadas de referencia. Guarda el plan, los IDs atendidos, el render y su evidencia en la campaña. Si intervienen ambos motores, entrega al segundo el MP4 del primero. |
| Revisión | Reproduce el máster con sonido. Comprueba por segundo la posición del ancla, la separación de los planos, los bordes, la lectura del texto y la sincronía. Devuelve cualquier defecto con tiempo e ID de orden. Vincula su dictamen al SHA-256 del máster exacto. |
| Analítica | Si la pieza se publica, vincula la variante y el efecto observado a la versión publicada. Para probar su aporte, compara piezas comparables y documenta qué otras variables cambiaron. |

Las marcas de voz de Whisper guían la tipografía. En un montaje instrumental, decide los acentos contra el ambiente y el movimiento visible. Usa las fuentes y colores de la cuenta dentro del plan y fija `usar_mi_estilo` en `false` para los planes de Tipografía del equipo. Así el resultado se puede reconstruir en otra estación.

## Ejemplo por escena

Fragmento de `guion/montaje-reel-NN.json` para un plano que comienza a 0 s en el video que recibe el motor. El reloj del original y el de la pieza se conservan por separado en la orden.

```json
{"id":"pulido-etiqueta","entrada":0.0,"salida":2.3,"herramienta":"efectos-converzzo","skill":"etiqueta-sigue","insumo":"plano-pulido.mp4","instruccion":"Seguir la punta verde con la caja del fotograma de referencia a 0.4 s.","resultado":"La línea toca la punta durante el movimiento y el texto deja ver el contacto."}
```

El editor guarda los parámetros del motor en `plan-efectos.json`. Los valores de este ejemplo corresponden a ese encuadre concreto.

```json
{"formato":"vertical","capas":[{"efecto":"etiqueta-sigue","desde":0.0,"hasta":2.3,"referencia":0.4,"caja":[0.57,0.56,0.81,0.69],"texto":"Punta de pulido"}]}
```

Ejecuta el render desde la raíz con las rutas reales de la campaña. Para una prueba de los modelos ya descargados se puede establecer `$env:HF_HUB_OFFLINE = "1"` durante el render. El archivo de evidencia del motor de Efectos incluye la pista en `_pista` o las profundidades en `_capas`, según la operación. Comprueba que la ejecución utilizó el modelo solicitado. El motor también dispone de seguimiento básico.

```powershell
python herramientas/converzzo.py render efectos-converzzo plano-pulido.mp4 plan-efectos.json con-efectos.mp4 --evidencia efectos-ejecutados.json
python herramientas/converzzo.py render tipografia-converzzo con-efectos.mp4 plan-textos.json master.mp4
```

La segunda operación usa un plan de Tipografía preparado por Edición. Para una foto de control, añade `--still 1.2` a una orden de render. Para tipos de subtítulo como `sub-karaoke`, consulta la ficha: el identificador de la skill y el nombre de la capa JSON pueden ser distintos.

Los motores, recursos y pesos se obtienen de sus fuentes al instalar. El repositorio incluye las licencias y los avisos de los dos paquetes. [Efectos de Converzzo](https://github.com/productoraudiovisual-droid/efectos-converzzo) · [Tipografía de Converzzo](https://github.com/productoraudiovisual-droid/tipografia-converzzo)
