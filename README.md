# MarketingIA

Equipo de agentes para convertir una hipótesis editorial en un reel y un carrusel de Instagram. Dirección elige el objetivo, Guion especifica cada toma y lámina, Video y Diseño trabajan en paralelo, y Revisión comprueba las exportaciones antes de que Publicación use el adaptador de Meta. El bibliotecario localiza planos y la memoria por cuenta conserva instrucciones, decisiones y resultados para la campaña siguiente.

## Instalar en otra PC

1. Instala Git, Python 3.11 o posterior, Node.js 20 o posterior y FFmpeg con FFprobe. Para delegar y clasificar imágenes, configura Codex y abre el proyecto en una sesión con acceso a los especialistas. Los trece perfiles están en `.codex/agents/`.
2. Clona el repositorio y prepara las dependencias desde su raíz. Estas instrucciones usan PowerShell en Windows. En macOS y Linux activa el entorno con `source .venv/bin/activate`.

   ```powershell
   git clone https://github.com/DaiVelasco/MarketingIA.git
   cd MarketingIA
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   npm ci
   ```

3. El exportador gráfico usa Chrome, Edge o Chromium instalado. Si hace falta el navegador, ejecuta `npx playwright-core install chromium`. El montaje profesional tiene sus propias dependencias de vídeo y comandos de instalación. [Plantilla de edición](herramientas/plantilla_reel/)
4. En `operacion.toml`, sustituye la cuenta de demostración, verifica la zona horaria, los formatos, las cuentas de referencia y el presupuesto aprobado. Completa la ficha de marca con sus fuentes. Coloca logos y materiales autorizados en el almacenamiento privado del equipo. [Ficha de marca](MARCA.md)
5. Configura por cuenta los servicios que se vayan a usar. Para voz se utiliza ElevenLabs, para editable de vídeo invideo y para diseño Canva. La edición local dispone de Whisper, Remotion y HyperFrames. Registra el acceso de los operadores a gbro-collage-broll y ClaudeAnimationBase para los efectos asignados por Guion. Las instrucciones del proyecto indican qué resultado debe dejar cada herramienta. Para el reconocimiento de voz opcional con Whisper de Python, instala `python -m pip install -r requirements-audio.txt`. [Edición y diseño](OPERACION.md)
6. Para lecturas o envíos con Meta, configura los valores en el gestor de credenciales del equipo y comprueba la identidad con `python instagram.py cuenta`. La distribución comienza en ensayo. El responsable de la cuenta decide el cambio a producción y las acciones habilitadas. [Conexión y publicación](INSTAGRAM.md)

## Primera prueba local

```powershell
python -B -m unittest discover -s pruebas
python radar.py demo
python campana.py iniciar --cuenta cuenta.demo --fecha 2030-01-15
python aprendizaje.py --cuenta cuenta.demo resumen
python biblioteca.py estado
```

La carpeta de jornada se crea en `campanas/cuenta.demo/2030-01-15/`. Guarda el brief, guion, carrusel y dictamen allí. La carpeta de video tiene tres destinos con nombres fijos.

```text
Videos del proyecto - Reel de Instagram/
  01 - Videos crudos/
  02 - Referencias/
  03 - Videos terminados/
```

Para probar un montaje desde cero, copia la escaleta de colores de `ejemplos/reel/` y llama al montador. Escribe un borrador con un título, un cambio de plano y un fundido en la carpeta privada de revisión.

```powershell
$jornada = "campanas/cuenta.demo/2030-01-15"
Copy-Item ejemplos/reel/escaleta.json "$jornada/guion/escaleta.json"
Copy-Item ejemplos/reel/pie-de-foto.txt "$jornada/guion/pie-de-foto.txt"
python campana.py producir $jornada --formato reel --borrador
```

En esa misma jornada puedes probar la validación del guion y la exportación de cuatro láminas y dos historias. El ejemplo genera figuras geométricas y texto de muestra en la carpeta privada de la jornada.

```powershell
python ejemplos/carrusel/preparar_demo.py $jornada
python campana.py validar-orden-carrusel $jornada --revision 1
node herramientas/exportar.cjs "$jornada/carrusel"
node herramientas/exportar.cjs "$jornada/carrusel" --verificar
```

## Operación autónoma

Abre la carpeta raíz como proyecto en Codex. Para una primera jornada pide al director que ejecute el ciclo de `AGENTS.md` y `OPERACION.md`. Dirección recupera el brief si la jornada ya existe y entrega a cada especialista su ruta de salida. Para pasar de la prueba a la operación recurrente, crea en tu instalación dos automatizaciones con esta carpeta como directorio de trabajo. Ajusta sus horarios al huso de la cuenta y mantén disponible un equipo con sus conectores.

| Frecuencia de ejemplo | Instrucción para la automatización |
|---|---|
| Diaria a las 09:00 locales | Ejecuta el ciclo de Dirección según AGENTS.md y OPERACION.md. Lee la memoria y el catálogo local, prepara ambos formatos, revisa la pieza y usa el modo de operacion.toml. Registra el estado y el siguiente responsable. |
| Cada hora | Ejecútate como Comunidad. Consulta comentarios de medios propios y el FAQ vigente, comprueba el modo y los permisos antes de responder. Registra los casos que requieren atención personal. |

El monitor de la biblioteca puede arrancar al iniciar sesión en Windows mediante `herramientas/instalar-bibliotecario.ps1`. También puede ejecutarse en primer plano con `python biblioteca.py vigilar`. Revisa sus requisitos y estados antes de activarlo en la nueva PC. [Biblioteca audiovisual](BIBLIOTECA.md)

## Guías y contratos

| Etapa | Documento |
|---|---|
| Investigación, decisiones, edición y control de calidad | [Operación diaria](OPERACION.md) y [perfiles y acuerdos del equipo](AGENTS.md) |
| Logo, voz, recursos y datos comerciales | [Ficha editable de la marca](MARCA.md) |
| Edición con voz y subtítulos | [Motor de producción del reel](herramientas/plantilla_reel/) |
| Orden del diseñador, imágenes y exportación de las láminas | [Carruseles e historias](herramientas/DISENO.md) |
| Clasificación de originales y referencias | [Manual de la biblioteca](BIBLIOTECA.md) |
| Revisión del administrador y propuestas por ronda | [Intercambio con el portal](herramientas/INTERCAMBIO.md) |
| Preferencias y resultados por cuenta | [Memoria editorial](APRENDIZAJE.md) y [reglas de la skill](skills/memoria-editorial/SKILL.md) |
| Credenciales y adaptador de Meta | [Instagram](INSTAGRAM.md) |

Las trece skills de Instagram se distribuyen con su licencia MIT original. El equipo puede leerlas directamente desde el proyecto. [Código de referencia](https://github.com/Jakeschincariol/instagram-agent-skill) · [Licencia](referencias/instagram-agent/LICENSE)
