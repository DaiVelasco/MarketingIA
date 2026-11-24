---
name: ficha
description: "Muestra una ficha de producto u outfit (nombre, detalles como talla, color o material, y precio) con una línea que señala el producto en el video. Úsala con /ficha y el video, o cuando pidan mostrar los detalles de un producto, prenda u outfit."
---

# /ficha

Ficha de producto u outfit: nombre, detalles (talla, color, material, ingredientes) y precio, con una línea animada que sale desde el producto. Para tiendas de ropa, belleza, tecnología o comida.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Úsala cuando la persona muestra o nombra un producto. Saca los detalles de lo que dice o de lo que la persona te escriba; nunca inventes precios ni características.
- Si se ve el producto, mira una foto de control y marca su posición en `punto` (x e y de 0 a 1). Si no, déjala sin `punto` y se ubica sola junto a la cara.
- Máximo 4 detalles cortos. Dura de 3 a 5 s.

## Capa
```json
{"efecto": "ficha", "desde": 4.8, "hasta": 8.0, "titulo": "Chaqueta denim", "detalles": ["Tallas S a XL", "100% algodón", "Azul clásico"], "precio": "$149.900", "punto": {"x": 0.55, "y": 0.62}}
```
Opciones: `titulo`, `detalles` (lista), `precio` (opcional), `punto` (`x`, `y` de 0 a 1; opcional).
Colores y fuentes salen del `estilo` del plan (ver GUIA.md).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
