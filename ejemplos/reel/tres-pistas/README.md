# Tres pistas

Capa editable de Remotion del reel «¿De qué marca es?». El faro, la pantalla y la palanca se dibujan sobre el video y pasan al marcador antes de que aparezca la marca. La composición tiene 336 cuadros a 30 fps y entrega transparencia en 1080 × 1920. El MP4 terminado incluye además la transición, la placa de Konduce y la mezcla de audio. [Ver la entrega del reel](https://github.com/DaiVelasco/MarketingIA/releases/tag/reel-tres-pistas-2026-11-25)

Desde la raíz del proyecto, instala los motores de Converzzo y renderiza una muestra o la capa completa.

```powershell
python herramientas/converzzo.py preparar
node ejemplos/reel/tres-pistas/render.cjs --still 85 previo.png
node ejemplos/reel/tres-pistas/render.cjs pistas.mov
```

El render usa las fuentes Archivo Black y Space Grotesk que prepara el motor de Tipografía. Puedes indicar la ubicación de Chrome o Chromium con `CONVERZZO_CHROME`. Si los motores ya están en otra instalación local, `CONVERZZO_MOTORES` admite la carpeta que contiene los dos motores.

Edita los textos, los intervalos y el marcador en `Pistas.jsx`. Cada entrada de `encuadres.json` contiene el trazo en un fotograma de referencia y cinco posiciones a lo largo de la toma. Para medir otro clip, adapta los tiempos y los contornos de `medir.py` y ejecútalo con el Python de Converzzo. El primer argumento es el video y el segundo es un JSON de salida nuevo. Revisa sus posiciones sobre las tres tomas antes de usarlo como `encuadres.json`.
