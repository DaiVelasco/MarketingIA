---
name: contorno-neon
description: "Dibuja una línea de luz neón alrededor de la persona o de un objeto que la sigue cuadro a cuadro. Úsala con /contorno-neon y el video, o cuando pidan contorno neón, borde de luz, outline o glow alrededor de la persona."
---

# /contorno-neon

Una línea brillante de color neón rodea la silueta de la persona (o de un objeto) y late suavemente. Llama mucho la atención en un gancho o un momento clave.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- En el gancho o en una frase fuerte, de 1,5 a 4 s. Funciona mejor sobre fondos oscuros o medios.
- Color: uno que contraste con el fondo y con la ropa (cian, magenta, verde lima, amarillo).

## Capa
```json
{"efecto": "contorno-neon", "desde": 0.4, "hasta": 3.2, "color": "#00E5FF"}
```
Opciones: `color` (hex, #00E5FF), `grosor` (1; de 0.5 a 3), `pulso` (latidos por segundo, 1.2), `sujeto` (`"objeto"` con `punto` o `caja`; por defecto la persona).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
