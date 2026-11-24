---
name: mockup-interfaz
description: "Muestra una interfaz animada genérica en el video: un chat con mensajes, notificaciones que caen o un prompt de IA que se escribe y responde. Úsala con /mockup-interfaz y el video, o cuando pidan mostrar un chat, una conversación, notificaciones, ventas que llegan o un prompt."
---

# /mockup-interfaz

Interfaces animadas genéricas (sin imitar apps reales): **chat** con burbujas que aparecen y "escribiendo…", **notificaciones** que caen desde arriba (ventas, pedidos, pagos) o **prompt** de IA que se escribe, se envía y responde.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Chat: para mostrar cómo se conversa con un cliente. Notificaciones: para "así me llegan los pedidos". Prompt: para mostrar qué pedirle a una IA.
- Los textos los da la persona o salen de lo que dice; nunca inventes cifras ni nombres de clientes reales.
- Cada mensaje o notificación puede tener `en` (segundo en que aparece). Dura de 3 a 7 s.

## Capa
```json
{"efecto": "mockup-interfaz", "desde": 6.4, "hasta": 10.4, "tipo": "chat", "nombre": "Laura", "mensajes": [{"de": "otro", "texto": "Hola, ¿tienen envíos?", "en": 6.9}, {"de": "yo", "texto": "¡Sí! A todo el país", "en": 7.9}]}
```
Opciones: `tipo` (`chat`, `notificacion`, `prompt`). Chat: `nombre`, `mensajes` (`de`: "yo" u "otro", `texto`, `en`). Notificación: `notificaciones` (`app`, `titulo`, `texto`, `en`). Prompt: `prompt` (`texto`, `respuesta`). `y` para fijar la altura.
Colores y fuentes salen del `estilo` del plan (ver GUIA.md).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
