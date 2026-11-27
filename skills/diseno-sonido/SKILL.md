---
name: diseno-sonido
description: >-
  Diseño de sonido profesional para reels, vídeos y animaciones de motion: pone los efectos (pops, barridos, clics,
  tecleo, éxito, risers, revelaciones) en el fotograma exacto de lo que se ve, con varias tomas que rotan para que no
  suene a máquina, estéreo por posición, secuencias que suben de tono, efectos que se apartan de la voz y máster a
  −14 LUFS con informe de calidad. Saca los sonidos de tu carpeta y de la API de Openverse (solo CC0 y CC BY, con su
  atribución). Úsala cuando digas "/diseno-sonido", "ponle sonido", "ponle efectos", "diseño de sonido", "los efectos
  suenan mal", "busca un efecto de…", o cuando un vídeo o una animación necesite efectos.
---

# Diseño de sonido

Motor: `scripts/diseno.py`. Sonidos: `scripts/openverse.py`. Necesitas `ffmpeg` y Python 3 con `numpy`.
El cliente de Openverse admite acceso anónimo o las variables de entorno `OPENVERSE_CLIENT_ID` y `OPENVERSE_CLIENT_SECRET`. Si Cloudflare intercepta una petición, el comando informa la ruta y el Ray ID y termina con error. En MarketingIA, la guía `integraciones/sonido/README.md` explica el registro de la aplicación y la descarga desde una ficha de Wikimedia Commons.
Los sonidos viven en `./sonidos/` del proyecto (o donde diga `SONIDOS_DIR`):
- `sonidos/<papel>/` → los tuyos, los que elijas a oído. Siempre van primero.
- `sonidos/openverse/<papel>/` → los bajados de Openverse, con `manifiesto.json` (autor, licencia, atribución).

Papeles: `texto`, `icono`, `pop`, `transicion`, `pantalla`, `clic`, `exito`, `secuencia`, `tecleo`, `tension`, `revelacion`, `cifra`.

## Flujo
1. **Lista los momentos que se ven**, sacados del código de la animación o de los cortes, nunca a ojo: qué aparece,
   en qué segundo y en qué `x` de la pantalla. Un papel para cada uno. Si no se ve nada, no suena nada.
2. **Llena los papeles que falten** (mínimo 3 tomas por papel, salvo el clic de UI):
   ```
   python3 scripts/openverse.py bajar --papel transicion "soft whoosh" "swish air" --n 3 --max-dur 1.6
   python3 scripts/openverse.py bajar --papel pop "soft pop" "bubble pop" --n 3 --max-dur 0.6
   python3 scripts/openverse.py recortar --papel tecleo "iphone typing"     # grabación larga → toques sueltos
   python3 scripts/diseno.py tomas transicion                               # qué hay y cuánto brilla cada una
   ```
   Fuera lo que suene agudo o barato: marca `"fuera": true` en el manifiesto.
3. **Mezcla**:
   ```python
   import sys; sys.path.insert(0, ".claude/skills/diseno-sonido/scripts"); import diseno
   eventos = [(0.12, "pop", {"x": 540}), (0.45, "transicion", {}),
              (2.62, "secuencia", {"paso": 0}), (2.80, "secuencia", {"paso": 1}), (2.98, "secuencia", {"paso": 2}),
              (5.05, "tension", {}), (5.05, "exito", {"x": 540}), (6.95, "revelacion", {})]
   diseno.mezclar(eventos, dur=8.5, salida="sfx.wav", voz=None)      # con voz: voz="voz.wav"
   ```
   Opciones por evento: `x` (0-1080, estéreo), `paso` (n.º en una secuencia: misma toma, +0,55 semitonos por paso),
   `toma` (fijar una toma concreta cuando ya te gustó una versión). `ganancia_db` sube o baja todos los efectos.
4. **Lee el informe** (`sfx.json` y la línea `[sonido]`): gestos cada 10 s, sonido en los 2 primeros segundos,
   huecos de más de 4 s, ráfagas repetidas, efectos que caen en la voz, LUFS y pico. Corrige hasta que no haya avisos.
5. **Monta** el WAV sobre el vídeo sin recodificar la imagen:
   `ffmpeg -i video.mp4 -i sfx.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest final.mp4`
6. **Créditos**: `python3 scripts/openverse.py creditos` → pégalos en la descripción (CC BY lo exige).

## Reglas (medidas)
| Qué | Valor |
|---|---|
| Densidad | ≤ 8 gestos cada 10 s con voz, ≤ 16 en motion sin voz (una ráfaga de pops o de teclas cuenta como uno) |
| Primer sonido | en los 2 primeros segundos |
| Hueco máximo sin sonido | 4 s |
| Variedad | ≥ 3 tomas por papel, nunca la misma dos veces seguidas, ±1,5 dB y ±0,4 semitonos |
| Clic de UI y tecleo | una sola voz (un teclado por vídeo), sin cambiar el tono |
| Colocación | secos por su llegada (primera ventana de 10 ms a 6 dB del máximo), barridos por su pico, risers terminando en el golpe |
| Desfases | texto −20 ms · clic −11 · icono +10 · pop +30 |
| Sobre la voz | si cae en plena sílaba: −3 dB y paso alto a 400 Hz; golpes grandes −9 dB |
| Estéreo | pan de potencia constante ±0,35 según la posición; nada en contrafase |
| Brillo | redondo antes que brillante: centroide ≤ 3,2 kHz (teclas ≤ 5,6, éxitos ≤ 4,5); filtro 90 Hz-8 kHz |
| Sonoridad | por papel, en ventanas de 0,4 s; los clics cortos llevan cola de sala para que se oigan |
| Máster | −14 LUFS con voz, −16 efectos solos; pico real ≤ −1 dBTP |

**Suena barato:** un barrido en cada corte (la mayoría de cortes no llevan sonido), golpe grave en el logo, reverb en
sonidos pequeños, tono aleatorio en el tecleo, clics de más de 150 ms, picos entre 2 y 6 kHz.

## Licencias
Openverse indexa Freesound, Jamendo y otros. La skill solo acepta CC0, dominio público y CC BY (fuera NC, ND, SA).
Comprueba la licencia en la ficha de cada sonido antes de un anuncio. Las reglas de colocación y mezcla salen de
estudiar dos proyectos abiertos de diseño de sonido para agentes, real-sfx (Clipwing) y earshot (Leon Lin, MIT); el
código de esta skill es propio.
