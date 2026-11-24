---
name: gancho
description: "Pone un título grande en los primeros segundos del video para enganchar, palabra por palabra y con una palabra resaltada. Úsala con /gancho y el video, o cuando pidan un gancho, hook, título al inicio o texto para enganchar."
---

# /gancho

Título grande al inicio que aparece palabra por palabra, con una palabra resaltada en caja de color. Se ubica arriba de la cara (o abajo si no hay espacio).

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Usa la primera frase del video o una versión más corta e impactante (máximo unas 8 palabras). Si la persona da el texto, úsalo tal cual.
- `resaltar`: la palabra clave (un número, "gratis", "error", "nunca", el beneficio).
- `desde` = 0,1; `hasta` = cuando termina la primera frase (2 a 4 s).

## Capa
```json
{"efecto": "gancho", "desde": 0.1, "hasta": 2.9, "texto": "WhatsApp quiere cobrarte", "resaltar": "cobrarte"}
```
Opciones: `texto`, `resaltar` (una o varias palabras), `y` (0 a 1 para fijar la altura). La fuente sale de `estilo.fuenteTitulo`.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
