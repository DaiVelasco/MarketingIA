---
name: cita
description: "Muestra una frase destacada con comillas grandes, en serif elegante, con autor y una palabra resaltada en cursiva. Úsala con /cita y el video, o cuando pidan resaltar una frase, cita, testimonio o reseña de un cliente."
---

# /cita

Frase destacada con comillas grandes, palabras que aparecen una por una, una palabra en cursiva de color y el autor abajo. Va en la parte baja con un degradado oscuro para que se lea.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Para la frase más importante del video, un testimonio o una reseña real de un cliente.
- Usa las palabras exactas de la persona o del cliente; nunca inventes testimonios.
- Dura de 3 a 6 s según el largo.

## Capa
```json
{"efecto": "cita", "desde": 12.0, "hasta": 16.5, "texto": "El mejor sérum que he probado en mi vida", "autor": "Laura, clienta", "resaltar": "mejor"}
```
Opciones: `texto`, `autor` (opcional), `resaltar` (palabras en cursiva de color), `color`, `fuente` (playfair por defecto), `tamano`, `posicion` / `y`.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
