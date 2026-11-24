---
name: antes-despues
description: "Muestra un antes y después en pantalla dividida con una barra deslizante, usando dos momentos del mismo video o dos fotos o videos que pase la persona. Úsala con /antes-despues y el video, o cuando pidan comparar el antes y el después de un resultado."
---

# /antes-despues

Antes y después con barra deslizante: la imagen del antes y la del después se dividen en pantalla y una barra las revela. Para resultados de belleza, limpieza, remodelación, outfits o ediciones.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Fuentes: dos instantes del mismo video (`antes_en`, `despues_en`, en segundos) o dos archivos que pase la persona (`antes_archivo`, `despues_archivo`: foto o video, con la ruta relativa al plan o absoluta).
- Si usa instantes del video, mira fotos de control para elegir el mejor cuadro de cada momento.
- Dura de 3 a 5 s. Ocupa toda la pantalla, así que en ese tramo no se ve el video normal.

## Capa
```json
{"efecto": "antes-despues", "desde": 12.8, "hasta": 16.2, "antes_en": 0.5, "despues_en": 14.0}
```
Opciones: `antes_en` / `despues_en` (segundos) o `antes_archivo` / `despues_archivo`, `division`: `"vertical"` (izquierda/derecha, por defecto) o `"horizontal"` (arriba/abajo), `quieto` (true = imágenes fijas; false = en movimiento), `etiquetas` (por defecto ["ANTES", "DESPUÉS"]).
Colores y fuentes salen del `estilo` del plan (ver GUIA.md).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
