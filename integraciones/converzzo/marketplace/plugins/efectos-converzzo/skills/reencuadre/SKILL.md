---
name: reencuadre
description: "Convierte un video horizontal en vertical 9:16 siguiendo la cara automáticamente. Úsala con /reencuadre y el video, o cuando pidan pasar un video horizontal a vertical o a formato Reels."
---

# /reencuadre

Pasa un video horizontal a vertical (9:16) y mueve el encuadre para que la cara quede siempre en el centro, como un camarógrafo siguiendo a la persona.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- Va en todo el video: `desde` 0 y `hasta` = duración del video.
- Si el video ya es vertical, avísale que no lo necesita.
- Si hay varias personas, sigue la cara más grande.

## Capa
```json
{"efecto": "reencuadre", "desde": 0, "hasta": 45.2}
```
Opciones: `posicion` (0.5 = cara al centro; 0.4 un poco a la izquierda), `suavidad` (0.6 s; más alto = movimiento más tranquilo).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
