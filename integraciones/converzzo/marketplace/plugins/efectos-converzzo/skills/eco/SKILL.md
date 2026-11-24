---
name: eco
description: "Deja una estela o eco de la persona o de un objeto que se mueve: copias que se van desvaneciendo detrás. Úsala con /eco y el video, o cuando pidan estela, eco, trail o efecto de movimiento."
---

# /eco

Detrás de la persona (o del objeto) quedan copias transparentes de los cuadros anteriores que se desvanecen, como una estela de movimiento.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- En un movimiento rápido (un giro, un salto, un gesto, un producto que pasa), de 1 a 3 s. Si no hay movimiento no se nota.

## Capa
```json
{"efecto": "eco", "desde": 3.0, "hasta": 4.8, "copias": 4, "separacion": 3}
```
Opciones: `copias` (4; de 1 a 8), `separacion` (cuadros entre copias, 3), `color` (opcional, brillo de color en la estela), `sujeto` (`"objeto"` con `punto` o `caja`; por defecto la persona).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
