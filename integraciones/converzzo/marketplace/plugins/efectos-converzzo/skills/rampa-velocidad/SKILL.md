---
name: rampa-velocidad
description: "Rampa de velocidad: el video pasa suave de velocidad normal a cámara lenta (o a rápido) y vuelve, como en los edits de acción y de producto. Úsala con /rampa-velocidad y el video, o cuando pidan speed ramp, rampa, frenar de golpe o cámara lenta que entra suave."
---

# /rampa-velocidad

La velocidad baja (o sube) de forma gradual hasta la velocidad elegida, se mantiene y vuelve a la normal, sin cortes. La cámara lenta queda fluida con cuadros intermedios.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- En un movimiento llamativo: un salto, un giro, un producto que cae o se sirve, un gesto. De 1 a 4 s.
- Va muy bien sobre el golpe de la música. El audio se estira; si molesta, `"audio": "silencio"` y música encima con `/musica`.

## Capa
```json
{"efecto": "rampa-velocidad", "desde": 3.2, "hasta": 5.0, "velocidad": 0.3}
```
Opciones: `velocidad` (0.3 = muy lenta; mayor que 1 = rampa hacia rápido, por ejemplo 3), `rampa` (segundos que tarda en frenar y en volver, 0.5), `audio` (`"lento"` o `"silencio"`), `fluido` (true). Los tiempos del plan van en el video original; el motor ajusta el resto. No se encima con otros efectos de tiempo.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
