---
name: musica
description: "Pone música de fondo al video que baja sola cuando la persona habla y sube en las pausas (ducking), con entrada y salida suaves. Úsala con /musica y el video, o cuando pidan música de fondo o una canción que no tape la voz."
---

# /musica

Música de fondo que baja sola cuando hay voz y sube en las pausas, con entrada y salida suaves. La persona pone su música (un archivo de audio); el pack no genera música.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Pide el archivo de música (mp3, wav, m4a). Recuerda que use música con permiso de uso (biblioteca libre de derechos o la de la red social al publicar).
- Normalmente va en todo el video. `volumen` 0,15 a 0,3 según qué tan presente la quiera.

## Capa
```json
{"efecto": "musica", "desde": 0, "hasta": 45.2, "musica_archivo": "cancion.mp3", "volumen": 0.22}
```
Opciones: `musica_archivo` (ruta relativa al plan o absoluta), `volumen` (0.22), `bajar_con_voz` (true).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
