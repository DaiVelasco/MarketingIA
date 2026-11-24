---
name: pixelar
description: "Pixela o desenfoca algo que no se debe ver en el video (un documento, una placa, una pantalla, una cara, un logo) y lo sigue aunque se mueva. Úsala con /pixelar y el video, o cuando pidan pixelar, censurar, tapar o difuminar algo."
---

# /pixelar

Tapa con pixeles (o desenfoque) un documento, una placa, una pantalla, un dato privado o una cara, y lo sigue cuadro a cuadro aunque la cámara o el objeto se muevan.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- En todo el tramo donde se ve lo que hay que tapar (si aparece desde el inicio, `desde` 0). Que sobre medio segundo antes y después.
- Para datos privados usa `"forma": "caja"`: tapa un rectángulo con margen alrededor y no deja asomar bordes.

## Marcar el objeto
Sigue la sección "Objetos" de GUIA.md: elige un segundo `referencia` donde se vea bien, saca ese cuadro en el formato final, míralo y marca el objeto con `"punto": [x, y]` (centro) o `"caja": [x0, y0, x1, y1]`, de 0 a 1. Si en las fotos de control se cuela algo (una mano), agrega `"negativos": [[x, y]]`. El motor lo sigue solo con SAM 2.1.

## Capa
```json
{"efecto": "pixelar", "desde": 0, "hasta": 4.0, "caja": [0.30, 0.25, 0.72, 0.80], "referencia": 1.5, "forma": "caja"}
```
Opciones: `punto` o `caja` (lo que se tapa), `negativos`, `referencia` (segundo en que valen), `estilo` (`"pixeles"` por defecto o `"desenfoque"`), `tamano` (tamaño del pixel, 24; más grande = más tapado), `forma` (`"mascara"`, la silueta, o `"caja"`, un rectángulo con margen), `objetos` (varias cosas a la vez). Sin SAM instalado tapa la caja fija (no la sigue).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
