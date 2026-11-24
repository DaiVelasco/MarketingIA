---
name: sub-detras
description: "Subtítulos gigantes detrás de la persona: la persona queda por delante y tapa parte del texto. Úsala con /sub-detras y el video, o cuando pidan subtítulos estilo detras."
---

# /sub-detras

Subtítulos gigantes detrás de la persona: la persona queda por delante y tapa parte del texto. Ideal para ganchos y frases cortas de mucho impacto visual (recorta a la persona sin pantalla verde). Fuente por defecto: Anton.

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
{"efecto": "subtitulos", "desde": 0, "hasta": 45.2, "estilo": "detras", "correcciones": {"wasap": "WhatsApp"}}
```
Opciones: `fuente` (cualquier fuente de `/fuentes` o un archivo .ttf/.otf), `color` (color de la palabra resaltada), `tamano`, `mayusculas` (true/false), `palabras_por_bloque`, `posicion` (`auto` debajo de la cara, `centro`, `arriba`) o `y` (0 a 1), `correcciones`, `idioma` ("es" por defecto), `frases` (subtítulos ya traducidos).

## Ojo
- Funciona mejor con frases cortas y con la persona quieta en el centro. Pon 1 o 2 palabras por bloque.
- No lo combines con zooms ni efectos de cámara en el mismo tramo (el recorte de la persona dejaría de coincidir).
- Tarda más en renderizar porque recorta a la persona en cada cuadro: úsalo en tramos de 3 a 15 s, no en todo un video largo.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
