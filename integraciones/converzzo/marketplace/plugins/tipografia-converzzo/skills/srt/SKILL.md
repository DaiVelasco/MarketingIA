---
name: srt
description: "Exporta los subtítulos del video como archivo .srt (para subirlo a YouTube, TikTok, Facebook o editarlo en CapCut o Premiere), con la transcripción revisada. Úsala con /srt y el video, o cuando pidan el archivo de subtítulos, srt, captions o la transcripción con tiempos."
---

# /srt

Saca el archivo .srt de un video (sin renderizar nada).

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Qué hacer
1. Corre: `cd .local/converzzo/motores/tipografia-converzzo/motor && node srt.mjs <video> <salida>.srt --idioma es`
   - `--por-bloque 7`: palabras máximas por subtítulo (7 por defecto; usa 3 o 4 para videos verticales con subtítulos cortos).
   - `--correcciones '{"wasap": "WhatsApp"}'`: arregla marcas o nombres mal transcritos.
2. Abre el .srt, revísalo y corrige errores evidentes de transcripción (nombres, marcas, cifras) antes de entregar. Puedes editarlo a mano.
3. Guárdalo junto al video, con el mismo nombre (`video.srt`), y entrégalo.
4. Recuérdale en una línea dónde subirlo: YouTube (Subtítulos → Subir archivo), TikTok y Facebook (subtítulos o captions al publicar), CapCut o Premiere (importar subtítulos).

Para el .srt en otro idioma usa `/traducir-subtitulos`.
