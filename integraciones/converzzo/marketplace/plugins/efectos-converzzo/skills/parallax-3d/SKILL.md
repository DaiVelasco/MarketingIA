---
name: parallax-3d
description: "Convierte un momento del video (o una foto) en una escena 3D: separa el fondo de lo cercano por profundidad y mueve la cámara para dar volumen, como una foto que cobra vida. Úsala con /parallax-3d y el video, o cuando pidan efecto 3D, parallax, foto 3D o 2.5D."
---

# /parallax-3d

Toma un cuadro del video (o una foto) y lo separa en capas por profundidad con IA. Al mover la cámara, lo cercano se mueve más que el fondo y la imagen gana volumen. Dura lo que dure la capa y luego vuelve al video.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- En un momento quieto y bonito: un plano del producto, un paisaje, una foto del local o del equipo, el cierre. De 2 a 4 s.
- Funciona mejor con algo claramente al frente y fondo detrás. En planos planos (una pared, un documento) no se nota.

## Capa
```json
{"efecto": "parallax-3d", "desde": 6.0, "hasta": 9.0, "en": 6.0}
```
Opciones: `en` (segundo del cuadro que se usa; por defecto `desde`) o `imagen_archivo` (una foto), `empuje` (1 = acercamiento; 0 = sin acercar), `lateral` (1 = paneo; 0 = sin paneo), `vertical` (0), `direccion` (`izquierda`/`derecha`), `capas` (3; de 2 a 5). El audio del video sigue sonando.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
