---
name: glitch
description: "Efecto glitch o falla digital en un tramo corto del video: los colores se separan y la imagen salta en franjas. Úsala con /glitch y el video, o cuando pidan glitch, falla digital, error o distorsión."
---

# /glitch

Falla digital a ráfagas: los colores se separan y la imagen salta en franjas. Sirve para remarcar un error, un problema, algo tecnológico o como transición.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Busca palabras como "error", "problema", "falla", "hackeo", "virus", "inteligencia artificial" o un cambio brusco.
- Dura de 0,3 a 0,8 s: más largo cansa.

## Capa
```json
{"efecto": "glitch", "desde": 13.5, "hasta": 14.0, "intensidad": 1}
```
Opciones: `intensidad` (1; de 0.5 a 2).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
