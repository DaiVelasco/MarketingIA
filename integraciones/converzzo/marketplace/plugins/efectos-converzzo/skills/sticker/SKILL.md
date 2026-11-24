---
name: sticker
description: "Convierte a la persona o un objeto del video en un sticker: borde blanco, sombra y un pequeño salto hacia adelante. Úsala con /sticker y el video, o cuando pidan efecto sticker, recorte con borde blanco o que algo salte de la pantalla."
---

# /sticker

La persona o el objeto sale como un sticker recortado con borde blanco y sombra, crece un poco y se inclina, y vuelve a su sitio al final.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- Para presentar un producto ("¡este es!") o en un momento divertido, de 1 a 3 s.

## Capa
```json
{"efecto": "sticker", "desde": 2.1, "hasta": 4.0, "sujeto": "objeto", "punto": [0.55, 0.52], "referencia": 2.5}
```
Opciones: `sujeto` (`"objeto"` con `punto` o `caja`; por defecto la persona), `escala` (1.08), `giro` (−4 grados), `borde` (1 = grosor), `color` (del borde, blanco).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
