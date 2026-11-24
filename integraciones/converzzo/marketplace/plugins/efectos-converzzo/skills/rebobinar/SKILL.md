---
name: rebobinar
description: "Efecto de rebobinar: el video retrocede rápido con look de cinta VHS y vuelve a reproducir el tramo. Úsala con /rebobinar y el video, o cuando pidan rewind, rebobinar, devolver o repetir una parte."
---

# /rebobinar

Rebobina un tramo con look de cinta VHS (líneas, ruido y "◀◀ REBOBINANDO") y lo vuelve a reproducir. Sirve para repetir un momento clave o para un "espera, ¿qué?".

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- `desde` y `hasta` marcan el tramo que se rebobina (en el video original): primero se ve normal, luego se rebobina hasta `desde` y se repite.
- Elige un tramo de 1,5 a 4 s con algo que valga la pena ver dos veces.

Los tiempos (`desde`, `hasta`) van siempre en el tiempo del video original, como salen en la transcripción: el motor los ajusta solo cuando el video cambia de duración.

## Capa
```json
{"efecto": "rebobinar", "desde": 6.6, "hasta": 8.6, "velocidad": 3, "repetir": true}
```
Opciones: `velocidad` del rebobinado (3; de 1.5 a 6), `repetir` (true = vuelve a reproducir el tramo; false = sigue después del rebobinado), `texto` (por defecto "REBOBINANDO").

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
