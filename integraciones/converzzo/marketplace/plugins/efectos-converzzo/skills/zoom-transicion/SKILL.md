---
name: zoom-transicion
description: "Transición de zoom: la cámara entra rápido hacia la imagen hasta el corte y sale abriendo, como pasar a través de la pantalla. Úsala con /zoom-transicion y el video, o cuando pidan una transición de zoom o zoom de paso."
---

# /zoom-transicion

Transición de zoom: entra rápido hacia la imagen hasta el punto del cambio y sale abriendo, con desenfoque de movimiento. Da sensación de "pasar a otra cosa".

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Ponla en un cambio de tema o de escena: `desde` = 0,3 s antes del cambio, `hasta` = 0,3 s después (0,5 a 0,8 s en total).

## Capa
```json
{"efecto": "zoom-transicion", "desde": 9.7, "hasta": 10.3, "zoom": 2.2}
```
Opciones: `zoom` (2.2; de 1.6 a 3).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
