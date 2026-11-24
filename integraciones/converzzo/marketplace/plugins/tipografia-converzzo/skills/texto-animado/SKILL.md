---
name: texto-animado
description: "Anima un texto libre con 9 animaciones: máquina de escribir, deslizar, rebote, ola, desenfoque, máscara, contorno, glitch o tipografía cinética. Úsala con /texto-animado y el video, o cuando pidan animar un texto, kinetic typography o un texto con movimiento."
---

# /texto-animado

Cualquier texto con una animación de entrada a elegir. Debajo de la cara por defecto, o arriba o al centro.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Para frases propias que la persona quiere en pantalla (un mensaje, una promesa, un tip, una lista corta).
- Elige la animación según el tono: `maquina` (historias, tecnología), `deslizar` (limpio, negocios), `rebote` (divertido, niños, comida), `ola` (alegre, verano), `desenfoque` (premium, belleza), `mascara` (elegante, cine), `contorno` (moda, deporte), `glitch` (tecnología, gaming), `cinetica` (una palabra a la vez, mucha energía).
- Dura de 2 a 5 s.

## Capa
```json
{"efecto": "texto-animado", "desde": 5.0, "hasta": 8.0, "texto": "Envíos gratis a todo el país", "animacion": "deslizar"}
```
Opciones: `texto` (usa `/` para partir líneas), `animacion`, `fuente` (cada animación trae una por defecto), `color`, `acento` (segundo color), `tamano`, `mayusculas`, `posicion` (`auto`, `arriba`, `centro`) o `y`, `fondo` (false para quitar la caja en `maquina`).

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
