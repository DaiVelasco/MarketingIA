---
name: look-pelicula
description: "Da al video un look de película completo: color de cine, halo en las luces, leve vaivén de la imagen, grano, viñeta y bandas negras. Úsala con /look-pelicula y el video, o cuando pidan que se vea cinematográfico, look de película, analógico o de cine."
---

# /look-pelicula

Look de película completo en un solo efecto: color de cine (sombras frías, luces cálidas, negros suaves), halo rojizo en las luces, un vaivén muy leve como de proyector, grano, viñeta y bandas negras arriba y abajo.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Puede ir en todo el video o en un tramo (un recuerdo, una historia). Entra y sale suave.
- No lo combines con `look` ni `grano` en el mismo tramo: ya los incluye.
- Si el video lleva textos importantes arriba o abajo, usa `"bandas": false` para que no los tapen.

## Capa
```json
{"efecto": "look-pelicula", "desde": 0, "hasta": 45.2, "intensidad": 1}
```
Opciones: `intensidad` (1; de 0.4 a 1), `bandas` (true), `transicion` (0.4 s).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
