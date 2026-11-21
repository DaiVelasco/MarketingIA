---
name: memoria-editorial
description: Aplica y actualiza la memoria editorial por cuenta de MarketingIA cuando el usuario corrige una pieza, el administrador elige entre propuestas o Instagram aporta resultados. Sirve también al director al preparar el siguiente reel o carrusel.
---

# Memoria editorial del equipo

Trabaja desde el proyecto MarketingIA que contiene `aprendizaje.py`. Al empezar un ciclo, lee `memoria/<cuenta>/MEMORIA.md`, la ficha de marca y la orden de la pieza. La memoria pertenece a la marca en ese proyecto y viaja con su copia. Un mismo equipo puede gestionar varias cuentas.

**Cuando el usuario corrige al equipo**, registra su indicación con `python aprendizaje.py --cuenta CUENTA registrar -` antes de cerrar la tarea. Para una instrucción, el JSON lleva `tipo` igual a `instruccion`, `id` estable y descriptivo, `formato` (`todos`, `reel` o `carrusel`), `directriz` fiel a sus palabras y `fuente` verificable. Si precisa o sustituye una regla, registra una revisión del mismo ID. Acota al encargo las decisiones que el usuario haya formulado solo para esa pieza. Conserva las indicaciones sobre las herramientas del editor, el branding, la organización del material y los traspasos entre agentes en el ámbito correspondiente.

**Cuando el administrador elige**, importa el resultado del portal contra el paquete que realmente vio. Registra la versión elegida y las alternativas disponibles. Guarda su motivo textual cuando lo facilite. Si solo hizo clic, describe lo que la pieza tiene de distinto y qué hipótesis conviene probar la próxima vez. Si cambian a la vez el formato, el tema y el diseño, esa selección por sí sola no permite aislar su razón. Contrasta varias elecciones comparables antes de describir una tendencia. La elección expresa gusto editorial. La publicación tiene su propio flujo en MarketingIA.

**Cuando llegan métricas**, vincula el ID publicado con la versión exacta, el formato y su cuenta. Usa la captura y la fecha reales. Consulta el resumen generado por `aprendizaje.py` para comparar vistas, me gusta y comentarios con piezas anteriores del mismo formato y edad. Si hay alcance, guardados o compartidos, conserva esos datos con su significado. Registra las métricas disponibles aunque la muestra aún sea pequeña. Describe un resultado por encima o por debajo de la referencia con el tamaño de la muestra y la métrica concreta. Formula el próximo ensayo como una hipótesis comprobable. Mantén los mandatos del usuario vigentes hasta que el usuario los cambie.

**Para la siguiente campaña**, el director selecciona una indicación vigente y, cuando haya evidencia suficiente, una hipótesis. El guionista las traduce a decisiones concretas por lámina o por escena. Diseño y Edición reciben la orden junto a sus archivos. Analítica guarda la prueba en el brief de la nueva campaña y vuelve a medir la publicación a una edad comparable. Usa `python aprendizaje.py --help` y `python portal.py --help` para consultar los comandos de la instalación.
