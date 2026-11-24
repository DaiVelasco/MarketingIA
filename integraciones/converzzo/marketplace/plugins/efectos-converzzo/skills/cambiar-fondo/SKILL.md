---
name: cambiar-fondo
description: "Recorta a la persona y le pone otro fondo (una foto, un video o un color) sin pantalla verde. Úsala con /cambiar-fondo y el video, o cuando pidan cambiar el fondo, quitar el fondo o poner otro fondo."
---

# /cambiar-fondo

Recorta a la persona y cambia el fondo por una foto, un video o un color plano, sin pantalla verde. Entra y sale suave.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Pide a la persona el fondo (foto o video) o un color. Si no tiene, sugiere un color de su marca.
- Funciona mejor con la persona sola, quieta y bien iluminada. Lo que sostiene en las manos puede verse cortado.
- Puede ir en todo el video o en un tramo.

## Capa
```json
{"efecto": "cambiar-fondo", "desde": 10.4, "hasta": 14.2, "fondo_archivo": "fondo.jpg"}
```
Opciones: `fondo_archivo` (foto o video; ruta relativa al plan o absoluta) o `color` (hex), `desenfoque` (px para desenfocar el fondo nuevo), `transicion` (0.35 s). `sujeto`: `"objeto"` para recortar un objeto (un plato, un producto, una bebida) en vez de la persona: las manos y el resto quedan fuera. Marca el objeto con `"punto": [x, y]` o `"caja": [x0, y0, x1, y1]` (0 a 1) en el segundo `referencia` y el motor lo sigue con SAM 2.1 (ver "Objetos" en GUIA.md). Tarda más.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
