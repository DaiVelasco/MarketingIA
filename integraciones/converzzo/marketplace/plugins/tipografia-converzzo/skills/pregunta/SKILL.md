---
name: pregunta
description: "Muestra una tarjeta tipo encuesta con una pregunta y opciones (con porcentajes si los da la persona) para invitar a comentar. Úsala con /pregunta y el video, o cuando pidan una encuesta, una pregunta al público o generar comentarios."
---

# /pregunta

Tarjeta blanca tipo encuesta con la pregunta y 2 a 4 opciones. Si hay porcentajes, las barras se llenan; si hay opción elegida, se ve un toque sobre ella.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Cuando la persona le pregunta algo al público ("¿tú cuál prefieres?", "cuéntame en comentarios") o al final para cerrar con interacción.
- Porcentajes solo si son reales (de una encuesta de historias, por ejemplo). Si no, ponla sin porcentajes.
- Dura de 3 a 5 s.

## Capa
```json
{"efecto": "pregunta", "desde": 30.2, "hasta": 34.5, "pregunta": "¿Cuál pides primero?", "opciones": ["Hamburguesa", "Pizza"]}
```
Opciones: `pregunta`, `opciones` (2 a 4), `porcentajes` (misma cantidad que opciones), `elegida` (número de opción que se toca, desde 0), `color`, `fuente`, `posicion` / `y`.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
