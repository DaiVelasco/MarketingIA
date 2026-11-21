# De un diseño a seis JPG

## Traspaso al agente que trabaja en Canva

La orden vive en `guion/carrusel-NN.json`, al lado del guion del reel. Lleva `cuenta`, `objetivo`, `cta`, `formato` igual a `[1080, 1350]` y cuatro entradas en `laminas`. Cada entrada indica `numero`, `titulo`, `cuerpo`, `imagen` (ruta del archivo dentro de la campaña), `recorte`, `capas` (lista de fondo a frente), `tipografia`, `posicion`, `control` y `alt`. Conserva en la campaña el fotograma elegido y documenta el reel y el segundo del que procede. Si el CTA ocupa una caja adicional, incluye su texto literal en la orden.

El guionista decide qué se lee y Dirección aprueba qué debe ver el lector. Diseño coloca el material de acuerdo con la orden en un documento 4:5, mantiene editables las cajas de texto y deja las fotos como objetos seleccionables. Revisión abre el diseño guardado en Canva y comprueba los textos, el encuadre, el orden de páginas y la legibilidad en móvil. Guarda el enlace de edición, la revisión de guion y cualquier diferencia con los archivos locales en `revision/`.

Antes de maquetar ejecuta `python campana.py validar-orden-carrusel CARPETA --revision 1`. Para una corrección después de cerrar la entrega, copia la orden al siguiente número y exporta esa revisión. Las entregas históricas conservan sus originales.

Dentro de la carpeta de cada campaña, guarda el pie de foto definitivo en `pie-de-foto.txt` y crea estos archivos.

```text
arte/
  01.html   Portada del carrusel
  02.html   Segunda lámina
  03.html   Tercera lámina
  04.html   Cierre del carrusel
  05.html   Primera historia
  06.html   Segunda historia
  recursos/ Fotos, tipografías, logo y estilos usados
```

Cada HTML es una pieza independiente, en UTF-8, con un único elemento `main` de 1080 × 1350 px para el carrusel o 1080 × 1920 px para las historias. Usa `body { margin: 0 }` y posiciona el contenido dentro de `main`. Las rutas de archivos son relativas al HTML, por ejemplo `recursos/portada.jpg`. Copia las fuentes y fotos necesarias al proyecto o elige una familia de sistema con alternativa. El exportador funciona sin conexión durante el render. Para imágenes con un recorte importante usa `object-fit: cover` y ajusta `object-position`. Si el arte final ya existe como imagen, puedes colocarlo en el HTML a tamaño final.

En las historias deja unos 250 px libres arriba y 320 px abajo para las barras de Instagram. En el carrusel reserva margen lateral para que los títulos sigan siendo legibles en el perfil. Comprueba el contraste con la fotografía y lee el texto en la vista reducida. Para detectar una palabra cortada, revisa la vista previa y el HTML.

Ejecuta desde la raíz, sustituyendo la ruta de ejemplo.

```sh
node herramientas/exportar.cjs campanas/mi.cuenta/2026-11-21/carrusel
node herramientas/exportar.cjs campanas/mi.cuenta/2026-11-21/carrusel --verificar
```

El directorio `entrega/` contiene las seis imágenes en `publicar/`, el texto del post, dos vistas previas y `instagram.zip` listo para entregar. Para corregir una entrega ya cerrada, ajusta el arte y añade `--revision 2` a ambos comandos. Obtendrás `entrega-v2/`. El programa conserva la versión anterior.

Instala Node.js 20 o posterior y ejecuta `npm ci` en la raíz. El exportador usa Playwright Core y JSZip. Detecta Chrome, Edge y Chromium o admite una ruta personalizada en `MARKETING_BROWSER`. Para obtener el Chromium de Playwright, ejecuta `npx playwright-core install chromium`. En Linux, el navegador necesita también sus bibliotecas de sistema.
