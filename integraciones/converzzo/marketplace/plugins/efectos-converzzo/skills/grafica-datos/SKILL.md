---
name: grafica-datos
description: "Muestra una gráfica animada con datos reales (barras, línea o dona) que crece mientras se habla de los resultados. Úsala con /grafica-datos y el video, o cuando pidan una gráfica, estadísticas, resultados, crecimiento o porcentajes en pantalla."
---

# /grafica-datos

Gráfica animada en una tarjeta: **barras** que crecen, **línea** que se dibuja o **dona** que se llena, con los valores contando. Resalta el dato más importante.

Parte del pack gratuito de efectos de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/efectos-converzzo/GUIA.md`.


## Cuándo ponerlo
- Úsala cuando la persona habla de resultados, crecimiento, ventas, seguidores o porcentajes.
- Los datos solo si la persona los dice o los escribe; nunca los inventes. Máximo 6 barras o puntos y 5 partes de dona.
- Barras para comparar, línea para mostrar evolución en el tiempo, dona para mostrar partes de un total.
- Dura de 3,5 a 6 s.

## Capa
```json
{"efecto": "grafica-datos", "desde": 2.2, "hasta": 6.2, "tipo": "barras", "titulo": "Seguidores por mes", "sufijo": "K", "datos": [{"etiqueta": "Ene", "valor": 120}, {"etiqueta": "Abr", "valor": 410}]}
```
Opciones: `tipo` (`barras`, `linea`, `dona`), `titulo`, `datos` (`etiqueta` + `valor`), `prefijo` ("$"), `sufijo` ("K", "%"), `decimales`, `destacar` (índice; por defecto el mayor), `fuente` (de dónde salen los datos), `y`.
Colores y fuentes salen del `estilo` del plan (ver GUIA.md).

Se puede combinar con cualquier otro efecto del pack en el mismo plan (ver GUIA.md).
