---
name: barrido
description: "Transición de barrido o whip pan: la imagen sale disparada hacia un lado con desenfoque de movimiento y vuelve a entrar, ideal en un corte o cambio de idea. Úsala con /barrido y el video, o cuando pidan whip pan, barrido o transición rápida."
---

# /barrido

Transición de barrido (whip pan): la imagen sale disparada hacia un lado con desenfoque de movimiento y entra de nuevo. Funciona en un corte o cuando la persona cambia de idea.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Busca cortes y cambios de idea: el inicio de una frase nueva después de una pausa, "pero", "ahora", "lo segundo".
- `desde` = 0,2 s antes del cambio; `hasta` = `desde` + 0,35 a 0,5 s. No más de 3 o 4 por video.

## Capa
```json
{"efecto": "barrido", "desde": 4.15, "hasta": 4.55, "direccion": "izquierda"}
```
Opciones: `direccion`: `"izquierda"` (por defecto) o `"derecha"`.

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
