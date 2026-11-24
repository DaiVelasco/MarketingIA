---
name: color-auto
description: "Corrige automáticamente la exposición y el balance de blancos de un video oscuro, amarillo o azulado. Úsala con /color-auto y el video, o cuando pidan corregir el color, arreglar la luz, que se vea más claro o quitar lo amarillo."
---

# /color-auto

Corrige solo la exposición y el balance de blancos: mide el color del video y lo ajusta con suavidad (solo corrige si de verdad hace falta). Se combina bien con `look`.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Normalmente va en todo el video: `desde` 0, `hasta` = duración, `"transicion": 0`.
- Si el video ya se ve bien, el efecto casi no cambia nada (es a propósito). Si la persona quiere más, sube `intensidad` o combina con un `look`.

## Capa
```json
{"efecto": "color-auto", "desde": 0, "hasta": 30.5, "transicion": 0}
```
Opciones: `intensidad` (1; de 0.3 a 1), `transicion` (0.3 s).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
