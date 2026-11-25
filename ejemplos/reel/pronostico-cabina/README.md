# El pronóstico de la cabina

Una presentadora da el parte del tiempo en Konduce. Al terminar «manguera», el plano cambia al chorro real que cae sobre un sedán. El reel dura 12,20 s en 1080 × 1920 a 30 fps.

El [guion](voz-reel-06.json) contiene las dos frases grabadas con CLARI en ElevenLabs. Esa misma grabación guio la boca de la presentadora de Genjutsu en Sync Lipsync 3 y se usó en la mezcla. Whisper dio los tiempos de los [subtítulos](subtitulos.srt). La [configuración de Converzzo](tipografia.json) conserva los tiempos por palabra y el estilo. El [pie de foto](pie-de-foto-reel-06.txt) acompaña el MP4.

La [escaleta](escaleta.json) conserva los intervalos de cada capa, el recorte del plano de agua y los cuadros de la placa.

| Tiempo | Montaje |
| --- | --- |
| 0,00–7,20 s | La presentadora dice el pronóstico frente a la cabina. El radar entra a los 2,10 s, a la altura del hombro, y sale a los 5,10 s. |
| 7,20–9,47 s | La manguera alcanza el techo del carro. El llamado «Mándaselo a tu copiloto» aparece debajo del chorro. |
| 9,47–9,60 s | El agua se funde con el primer fotograma de la placa durante cuatro cuadros. |
| 9,60–12,20 s | La firma ocupa los últimos 78 cuadros. La música del cierre original entra a los 9,71 s. |

## Editar los gráficos

El [archivo de Remotion](Parte.jsx) contiene el radar con la nube y el carro (`RadarCabina`, 90 cuadros) y el llamado a compartir (`Copiloto`, 68 cuadros). Cada composición se exporta con transparencia. Desde la raíz del repositorio, con los motores de Converzzo instalados, ejecuta estos comandos.

```powershell
python herramientas/converzzo.py preparar
node ejemplos/reel/pronostico-cabina/render.cjs RadarCabina radar.mov
node ejemplos/reel/pronostico-cabina/render.cjs Copiloto copiloto.mov
```

Para revisar un solo cuadro, usa `node ejemplos/reel/pronostico-cabina/render.cjs RadarCabina --still 30 radar.png`. El render usa Archivo Black y Space Grotesk del motor de tipografía. Puedes indicar la instalación de los motores mediante `CONVERZZO_MOTORES` y el ejecutable del navegador con `CONVERZZO_CHROME`.

## Comprobar la entrega

El MP4 aprobado tiene 366 cuadros y audio AAC estéreo a 48 kHz. En cuatro tramos del máster, la voz coincidió con la grabación de CLARI con 0 ms de desfase medido. Revisión también comprobó a escala de teléfono cómo se cierran los labios en la «p» de «para» y en la «m» de «manguera». La huella SHA-256 del archivo es `aa56f134f3203c2f2bb1671fe98b63e6510183f5d3bb0c758a98fe6a320fad4b`.
