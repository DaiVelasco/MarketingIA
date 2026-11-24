---
name: cta-whatsapp
description: "Pone un llamado a la acción para escribir por WhatsApp: botón verde con número que aparece y se toca, ideal al final del video. Úsala con /cta-whatsapp y el video, o cuando pidan un CTA, llamado a la acción, botón de WhatsApp o \"escríbenos\"."
---

# /cta-whatsapp

Botón verde de "Escríbenos por WhatsApp" con el número, un pulso que llama la atención y un toque animado. Ideal para cerrar videos de venta.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Normalmente va al final: los últimos 2 a 4 s, o cuando la persona dice "escríbenos", "pide el tuyo", "link", "WhatsApp".
- Usa el texto que diga la persona ("Pide el tuyo por WhatsApp"). El número solo si la persona te lo da; nunca lo inventes.

## Capa
```json
{"efecto": "cta-whatsapp", "desde": 26.5, "hasta": 30.0, "texto": "Pídelo por WhatsApp", "numero": "300 123 4567"}
```
Opciones: `texto`, `numero` (opcional), `subtexto` (opcional, por ejemplo "Envíos a todo el país"), `color` (verde por defecto), `y`.
Colores y fuentes salen del `estilo` del plan (ver GUIA.md).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
