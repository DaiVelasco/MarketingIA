---
name: mi-estilo
description: "Guarda las fuentes y colores de la marca de la persona para que todos sus subtítulos y textos salgan siempre con su estilo. Úsala con /mi-estilo o cuando pidan guardar su estilo, sus colores de marca, su fuente o su identidad visual."
---

# /mi-estilo

Guarda el estilo de marca (fuentes y colores) para que se aplique solo en todos los videos.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Qué hacer
1. Pregunta o saca el estilo de lo que la persona tenga: su logo, una captura de su feed, su manual de marca o una descripción ("rosado y elegante"). Mira las imágenes tú mismo y saca los colores en hex.
2. Propón (y muestra en una tabla corta para que la persona apruebe):
   - `fuenteTitulo`: títulos, ganchos y palabras grandes.
   - `fuente`: textos pequeños, etiquetas y tarjetas.
   - `fuenteSubtitulos` (opcional): si la pone, todos los estilos de subtítulos usan esa fuente. Si no, cada estilo usa la suya.
   - `acento`: color principal (cajas, botones, barras).
   - `sticker`: color de resaltado (la palabra que se dice, palabras clave).
   - `stickerTexto`: color del texto encima del resaltado (que contraste).
   - `texto` y `fondo`: texto oscuro y fondo claro de las tarjetas.
   Las fuentes salen del catálogo (`/fuentes`) o de un archivo propio.
3. Si la persona da un archivo de fuente propio, cópialo a `referencias/marca/<cuenta>/fuentes/` y usa su ruta completa.
4. Escribe `memoria/<cuenta>/estilo-converzzo.json`, por ejemplo:
```json
{"fuenteTitulo": "playfair", "fuente": "poppins", "fuenteSubtitulos": "poppins", "acento": "#C8507A", "sticker": "#F7C8D8", "stickerTexto": "#3A1020", "texto": "#2B2B2B", "fondo": "#FFF8F5"}
```
5. Si la persona tiene un video a mano, haz una foto de control con un `gancho` y `/sub-caja` para que vea cómo queda.

## Aplicar en una campaña

Guion incorpora el estilo de la cuenta al objeto `estilo` del plan de Tipografía, con `usar_mi_estilo: false`. Los ajustes específicos de la escena prevalecen. Conserva en la carpeta de la cuenta las fuentes y el archivo de estilo.
