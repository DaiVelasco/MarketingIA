---
name: grano
description: "Agrega grano de película al video para darle textura analógica o de cine. Úsala con /grano y el video, o cuando pidan grano, textura de película, look analógico o fílmico."
---

# /grano

Grano de película: una textura fina que se mueve cada cuadro y le da un look analógico o de cine. Queda muy bien con `look` cine o vintage.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Normalmente va en todo el video. Si la persona quiere solo una parte, ponlo en ese tramo.

## Capa
```json
{"efecto": "grano", "desde": 0, "hasta": 30.5, "intensidad": 1}
```
Opciones: `intensidad` (1; de 0.5 sutil a 2 fuerte).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
