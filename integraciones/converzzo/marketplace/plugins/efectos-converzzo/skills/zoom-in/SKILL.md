---
name: zoom-in
description: "Zoom marcado y suave hacia la cara en una palabra clave de un video vertical u horizontal. Úsala con /zoom-in y el video, o cuando pidan un zoom, punch-in o acercamiento rápido."
---

# /zoom-in

Zoom marcado y suave hacia la cara justo en una palabra. Es el recurso más usado para remarcar una idea.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- Si la persona dice la palabra, úsala. Si no, transcribe y elige 2 a 4 palabras fuertes: números, precios, "gratis", "nunca", "secreto", el remate de una frase.
- `desde` = inicio de la palabra − 0,05 s. `hasta` = final de esa frase o la siguiente pausa (de 1 a 3 s).

## Capa
```json
{"efecto": "zoom-in", "desde": 2.76, "hasta": 4.2, "zoom": 1.25}
```
Opciones: `zoom` (1.25; de 1.1 a 1.5), `rapidez` (0.45 s que tarda en llegar; 0.25 más rápido, 0.7 más lento), `volver`: `"corte"` (vuelve de golpe, por defecto) o `"suave"`.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
