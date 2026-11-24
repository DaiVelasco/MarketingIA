---
name: capitulo
description: "Pone un separador de sección (Parte 2, Paso 3, Error 1) con etiqueta de color y título, arriba de la cara o a pantalla completa. Úsala con /capitulo y el video, o cuando pidan dividir el video en partes, capítulos, pasos o secciones."
---

# /capitulo

Separador de sección: etiqueta de color ("PARTE 2") y título que entra deslizándose, arriba de la cara. En modo `pantalla` es una cortina de color a pantalla completa con el número gigante de fondo.

Parte del plugin gratuito de tipografía de Converzzo (@converzzo).

## Primero
Desde la raíz de MarketingIA, sigue `integraciones/converzzo/README.md` y la orden de la escena. La guía del motor está en `.local/converzzo/motores/tipografia-converzzo/GUIA.md`.

## Cuándo ponerlo
- Cuando la persona cambia de tema o enumera ("lo segundo…", "error número 3…").
- Dura de 1,5 a 3 s. En modo `pantalla`, máximo 1,5 s para no perder a la persona.

## Capa
```json
{"efecto": "capitulo", "desde": 21.3, "hasta": 23.8, "etiqueta": "Paso 2", "titulo": "Limpia tu piel"}
```
Opciones: `etiqueta`, `titulo`, `modo` (`barra` por defecto o `pantalla`), `color`, `fondo_color` (modo pantalla), `fuente`, `y`.

Se puede combinar con cualquier otro texto del plugin en el mismo plan (ver GUIA.md).
