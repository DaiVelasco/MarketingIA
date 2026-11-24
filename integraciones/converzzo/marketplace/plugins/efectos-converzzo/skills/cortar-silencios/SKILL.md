---
name: cortar-silencios
description: "Corta automáticamente los silencios y pausas largas de un video hablado, con un zoom alterno en cada corte para que no se note el salto. Úsala con /cortar-silencios y el video, o cuando pidan quitar silencios, quitar pausas, jump cuts o hacer el video más ágil."
---

# /cortar-silencios

Quita las pausas largas entre frases (y el silencio del inicio y del final) usando la transcripción, y alterna un leve zoom en cada corte para que el salto no se note. Es el primer paso de casi toda edición.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Va en todo el video: `desde` 0, `hasta` = duración.
- `umbral`: cuánto debe durar una pausa para cortarla (0,45 s por defecto; 0,3 para un ritmo muy ágil, 0,7 para algo más natural).
- Los demás efectos del plan siguen en el tiempo del video original: el motor los ajusta solos.
- Avísale cuántos segundos se quitaron (lo imprime el render).

## Capa
```json
{"efecto": "cortar-silencios", "desde": 0, "hasta": 45.2, "umbral": 0.45}
```
Opciones: `umbral` (0.45 s), `margen` (0.12 s de aire antes y después de cada frase), `zoom_alterno` (true; false = cortes secos), `zoom` (1.08).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
