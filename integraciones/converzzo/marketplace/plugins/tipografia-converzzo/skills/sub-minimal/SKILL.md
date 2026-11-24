---
name: sub-minimal
description: "Subtítulos discretos: letra fina, sin borde, abajo, y las palabras dichas se iluminan. Úsala con /sub-minimal y el video, o cuando pidan subtítulos estilo minimal."
---

# /sub-minimal

Subtítulos discretos: letra fina, sin borde, abajo, y las palabras dichas se iluminan. Ideal para marcas premium, belleza, arquitectura, videos tranquilos. Fuente por defecto: Inter Medium.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Va en todo el video: `desde` 0, `hasta` = duración (o solo el tramo que pida la persona). El motor transcribe solo.
- Revisa la transcripción: marcas, nombres o palabras mal escritas se arreglan en `correcciones` (`{"wasap": "WhatsApp"}`).
- Si el video tiene un `gancho` o un texto grande al inicio, empieza los subtítulos después para que no se pisen.
- Para subtítulos en otro idioma usa `/traducir-subtitulos`.

## Capa
```json
{"efecto": "subtitulos", "desde": 0, "hasta": 45.2, "estilo": "minimal", "correcciones": {"wasap": "WhatsApp"}}
```
Opciones: `fuente` (cualquier fuente de `/fuentes` o un archivo .ttf/.otf), `color` (color de la palabra resaltada), `tamano`, `mayusculas` (true/false), `palabras_por_bloque`, `posicion` (`auto` debajo de la cara, `centro`, `arriba`) o `y` (0 a 1), `correcciones`, `idioma` ("es" por defecto), `frases` (subtítulos ya traducidos).

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
