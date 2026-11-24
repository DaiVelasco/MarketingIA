---
name: acelerar
description: "Acelera un tramo del video (x2, x4…) para pasar rápido por una parte larga, como un time-lapse. Úsala con /acelerar y el video, o cuando pidan acelerar, adelantar, fast forward o timelapse."
---

# /acelerar

Acelera un tramo para pasar rápido por algo largo: un proceso, un antes y después, una preparación. Opcionalmente muestra una etiqueta "x2".

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Úsala en partes sin voz importante (procesos, armado, preparación).
- Si hay voz, la voz también se acelera; sugiere `"audio": "silencio"` si no se necesita.

Los tiempos (`desde`, `hasta`) van siempre en el tiempo del video original, como salen en la transcripción: el motor los ajusta solo cuando el video cambia de duración.

## Capa
```json
{"efecto": "acelerar", "desde": 10.1, "hasta": 13.0, "velocidad": 2, "etiqueta": "x2"}
```
Opciones: `velocidad` (2; de 1.25 a 8), `audio`: `"rapido"` (por defecto) o `"silencio"`, `etiqueta` (texto opcional como "x4").

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
