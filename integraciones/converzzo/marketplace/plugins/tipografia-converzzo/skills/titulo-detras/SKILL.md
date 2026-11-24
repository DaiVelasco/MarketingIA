---
name: titulo-detras
description: "Pone un título gigante detrás de la persona: las letras suben desde abajo y la persona queda por delante, sin pantalla verde. Úsala con /titulo-detras y el video, o cuando pidan texto detrás de la persona, título detrás o efecto de profundidad."
---

# /titulo-detras

Título enorme (1 a 3 palabras) detrás de la persona: las letras suben una por una y la persona tapa parte del texto, como en las portadas de revista.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Ideal al inicio (gancho visual) o para presentar un tema: el nombre de la marca, del producto o la idea principal en 1 a 3 palabras.
- Dura de 2 a 4 s. Mejor con la persona quieta y en el centro.
- No lo combines con zooms en el mismo tramo.

## Capa
```json
{"efecto": "titulo-detras", "desde": 0.2, "hasta": 3.0, "texto": "Glow Skin"}
```
Opciones: `texto` (usa `/` para partir líneas: "Nueva/Colección"), `fuente` (anton por defecto; también van bien bebas-neue, archivo-black, playfair, cinzel), `color`, `linea_color` (número de línea, desde 0, que va en el color de acento), `mayusculas`, `tamano`, `y` (centro del texto, 0 a 1).

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
