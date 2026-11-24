---
name: tallas-colores
description: "Muestra las tallas y colores disponibles de una prenda o producto en una tarjeta animada, marcando las agotadas. Úsala con /tallas-colores y el video, o cuando pidan mostrar tallas, colores disponibles o variantes."
---

# /tallas-colores

Tarjeta con las tallas (con las agotadas tachadas) y los colores disponibles con sus muestras. Para tiendas de ropa, calzado y accesorios.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Úsala cuando la persona dice las tallas o colores ("viene en S, M y L", "en negro y beige"). Solo los que diga o escriba.
- Colores por nombre (negro, blanco, beige, café, rojo, azul, verde oliva, rosado…) o con su hex. Dura de 3 a 5 s.

## Capa
```json
{"efecto": "tallas-colores", "desde": 7.8, "hasta": 11.0, "titulo": "Camiseta básica", "tallas": ["S", "M", "L", "XL"], "agotadas": ["XL"], "colores": ["negro", "blanco", "beige"]}
```
Opciones: `titulo`, `tallas`, `agotadas`, `colores` (nombres o `{nombre, hex}`), `y`.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
