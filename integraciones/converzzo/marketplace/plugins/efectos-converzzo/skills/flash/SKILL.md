---
name: flash
description: "Destello blanco (o de color) en un corte o cambio de idea de un video. Úsala con /flash y el video, o cuando pidan un flash, destello o transición con luz."
---

# /flash

Un destello que entra rápido y se apaga suave. Funciona como transición en un corte, al cambiar de idea o para remarcar un número o un remate.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Busca los cortes y cambios de idea: el inicio de una frase nueva después de una pausa, "pero", "entonces", "ahora".
- `desde` = el instante del corte. `hasta` = `desde` + 0,3 a 0,5 s.
- No más de 3 o 4 por video para que no canse.

## Capa
```json
{"efecto": "flash", "desde": 8.2, "hasta": 8.55, "color": "#FFFFFF"}
```
Opciones: `color` (blanco por defecto; cualquier color en hex), `intensidad` (1; de 0.4 a 1).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
