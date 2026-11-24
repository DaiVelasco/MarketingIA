---
name: sacudida
description: "Temblor o sacudida de cámara en un golpe o momento fuerte de un video. Úsala con /sacudida y el video, o cuando pidan camera shake, temblor o impacto."
---

# /sacudida

Temblor de cámara corto que remarca un golpe: una palabra fuerte, un aplauso, un corte de música.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.

## Cuándo ponerlo
- Si la persona dice la palabra, úsala. Si no, transcribe y busca la palabra más fuerte o el remate ("problema", "nunca", "boom").
- `desde` = inicio de la palabra − 0,03 s. `hasta` = `desde` + 0,4 a 0,8 s.
- Úsalo solo si la persona lo pide: no lo agregues por tu cuenta.

## Capa
```json
{"efecto": "sacudida", "desde": 13.52, "hasta": 14.1, "intensidad": 1}
```
Opciones: `intensidad` (1; de 0.5 suave a 2 fuerte).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
