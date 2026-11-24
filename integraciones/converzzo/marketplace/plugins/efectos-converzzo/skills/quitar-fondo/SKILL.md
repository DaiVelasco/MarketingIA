---
name: quitar-fondo
description: "Quita el fondo del video y lo entrega con transparencia (.mov ProRes 4444 o .webm) para usar a la persona o al producto en cualquier editor, sin pantalla verde. Úsala con /quitar-fondo y el video, o cuando pidan quitar el fondo, video sin fondo, transparente, alfa o recortar a la persona para editar."
---

# /quitar-fondo

Entrega el video con la persona (o un objeto) sola y el fondo transparente, listo para ponerla encima de cualquier cosa en Premiere, Final Cut, DaVinci, CapCut o After Effects.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- En todo el tramo que la persona quiera usar (normalmente todo el video: `desde` 0, `hasta` = duración).
- Si su editor no lee transparencias, ofrécele un fondo de color plano: `"fondo": "#00FF00"` (verde para hacer clave) o el color de su marca.

## Capa
```json
{"efecto": "quitar-fondo", "desde": 0, "hasta": 15.0}
```
Opciones: `sujeto` (`"persona"` por defecto, `"objeto"` con `punto` o `caja`, o `"verde"` si el video ya tiene pantalla verde), `fondo` (color hex en vez de transparencia).
Salida: con transparencia el archivo sale como **.mov (ProRes 4444)**, pesado pero compatible con todos los editores. Si la persona lo quiere para web, pon la salida con extensión `.webm`. Avísale que el archivo es grande.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
