---
name: dato
description: "Muestra un número que sube contando (+30.000, 97%, $2,5M) con una etiqueta, justo cuando se menciona en el video. Úsala con /dato y el video, o cuando pidan resaltar una cifra, un número o una estadística."
---

# /dato

Un número grande que sube contando con su etiqueta ("+30.000 alumnos"), en el momento en que la persona lo dice.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Úsalo cuando la persona dice una cifra importante. El valor tal cual se escribe en su país (`+30.000`, `97%`, `$2,5M`).
- Nunca inventes cifras. `desde` = cuando empieza a decir el número; dura de 2,5 a 4 s.

## Capa
```json
{"efecto": "dato", "desde": 14.4, "hasta": 17.4, "valor": "+30.000", "etiqueta": "alumnos en LATAM"}
```
Opciones: `valor`, `etiqueta`, `desde_valor` (desde qué número cuenta; 0 por defecto), `y`.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
