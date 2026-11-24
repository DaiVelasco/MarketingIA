---
name: zoom-out
description: "Efecto de zoom out: el video arranca cerca de la cara y se abre el plano para revelar. Úsala con /zoom-out y el video, o cuando pidan alejar, abrir el plano o revelar."
---

# /zoom-out

El plano arranca cerca y se va abriendo. Sirve para revelar algo (un producto, el lugar, un resultado) o para empezar un video con intriga.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- Úsalo al inicio del video o cuando la persona dice "mira", "esto es", "así quedó".
- Dura de 1,5 a 3 s.

## Capa
```json
{"efecto": "zoom-out", "desde": 0, "hasta": 2.4, "zoom": 1.45}
```
Opciones: `zoom` (1.45; de 1.2 a 1.8).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
