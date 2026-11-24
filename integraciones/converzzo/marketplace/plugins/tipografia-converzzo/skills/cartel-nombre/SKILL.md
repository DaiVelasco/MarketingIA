---
name: cartel-nombre
description: "Pone el nombre y cargo de quien habla en un cartel inferior (lower third) que entra con una barra de color. Úsala con /cartel-nombre y el video, o cuando pidan poner el nombre, presentar a alguien, lower third o cartel de nombre."
---

# /cartel-nombre

Cartel con nombre, cargo y usuario (lower third) que entra con una barra de color y se va solo. Para presentar a quien habla o a un invitado.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Ponlo cuando la persona se presenta ("soy…", "mi nombre es…") o en los primeros 2 a 5 s si no lo dice.
- Nombre y cargo solo si la persona los dice o te los da. Dura de 3 a 4 s.

## Capa
```json
{"efecto": "cartel-nombre", "desde": 1.0, "hasta": 4.5, "nombre": "Ana Gómez", "cargo": "Fundadora de Ana Cosméticos", "usuario": "@anacosmeticos"}
```
Opciones: `nombre`, `cargo`, `usuario` (opcional), `y`.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
