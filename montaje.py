"""Montaje vertical de clips, fotos y rótulos. Python 3.11+ y FFmpeg con libx264 y libass."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
from herramientas.entrega_archivos import publicar_archivo

W, H, FPS = 1080, 1920, 30
STYLE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Texto,Arial,64,&H00FFFFFF,&H00FFFFFF,&H00141010,&H90141010,-1,0,0,0,100,100,0,0,1,5,1,2,108,190,490,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


def source(folder, relative):
    path = Path(relative)
    if path.is_absolute():
        raise ValueError("El proyecto usa rutas relativas para poder trasladarse.")
    result = (folder / path).resolve()
    if not result.is_file():
        raise ValueError(f"No existe el recurso {relative}.")
    return str(result)


def render(plan_file, output, ffmpeg, temp_parent=None):
    plan = json.loads(plan_file.read_text(encoding="utf-8-sig"))
    folder = plan_file.resolve().parent
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    shots = plan["escenas"]
    if not shots:
        raise ValueError("La escaleta requiere al menos una escena.")
    with tempfile.TemporaryDirectory(dir=temp_parent or output.parent) as temp:
        work = Path(temp)

        def ff(*args):
            subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args], cwd=work, check=True)

        total_frames = 0
        parts = []
        for i, shot in enumerate(shots):
            seconds = float(shot["segundos"])
            if not math.isfinite(seconds) or not 0.2 <= seconds <= 90:
                raise ValueError("La duración de cada escena debe estar entre 0.2 y 90 segundos.")
            frames = round(seconds * FPS)
            total_frames += frames
            duration = frames / FPS
            text = str(shot.get("texto", "")).strip()
            if any(c in text for c in "{}\\"):
                raise ValueError("Los rótulos admiten texto simple y saltos de línea.")
            lines = [line for para in text.splitlines() for line in textwrap.wrap(para, 25)]
            if len(lines) > 3:
                raise ValueError(f"Acorta el rótulo de la escena {i + 1}.")
            asset = shot.get("archivo")
            if asset:
                src = source(folder, asset)
                still = Path(src).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
                start = float(shot.get("inicio", 0))
                if start < 0 or not math.isfinite(start):
                    raise ValueError("inicio debe ser un segundo válido.")
                inputs = ["-loop", "1", "-framerate", str(FPS)] if still else ["-ss", str(start)]
                inputs += ["-i", src]
            else:
                color = shot.get("color", "#183B40")
                if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                    raise ValueError("color requiere #RRGGBB.")
                inputs = ["-f", "lavfi", "-i", f"color=c=0x{color[1:]}:s={W}x{H}:r={FPS}"]
                still = True
            filters = [f"fps={FPS}", f"scale={W}:{H}:force_original_aspect_ratio=increase",
                       f"crop={W}:{H}", "setsar=1"]
            movement = shot.get("efecto", "corte")
            if movement == "acercamiento" and still:
                filters.append(f"zoompan=z='1+0.09*on/{max(1,frames-1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS}")
            elif movement == "fundido":
                filters.append(f"fade=t=in:st=0:d={min(.2, duration / 3):.3f}")
            elif movement != "corte":
                raise ValueError("Usa corte, fundido o acercamiento para imágenes.")
            subfile = f"rotulo{i}.ass"
            if lines:
                centis = round(duration * 100)
                end = f"0:{centis//6000:02d}:{centis//100%60:02d}.{centis%100:02d}"
                event = f"Dialogue: 0,0:00:00.00,{end},Texto,,0,0,0,," + r"\N".join(lines) + "\n"
                (work / subfile).write_text(STYLE + event, encoding="utf-8-sig")
                filters.append(f"ass={subfile}")
            part = f"plano{i}.mp4"
            ff(*inputs, "-vf", ",".join(filters), "-an", "-frames:v", str(frames), "-threads", "4", "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", part)
            parts.append(part)
        (work / "lista.txt").write_text("".join(f"file '{p}'\n" for p in parts), encoding="ascii")
        audio = plan.get("audio")
        if audio:
            audio_args = ["-i", source(folder, audio), "-map", "0:v", "-map", "1:a", "-af", "apad",
                          "-t", str(total_frames / FPS), "-c:a", "aac", "-ar", "48000", "-b:a", "160k"]
        else:
            audio_args = ["-an"]
        ff("-f", "concat", "-safe", "0", "-i", "lista.txt", *audio_args, "-c:v", "copy", "-movflags", "+faststart", "final.mp4")
        verified = subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-progress", "pipe:1", "-i", "final.mp4",
                                   "-map", "0:v", "-map", "0:a?", "-f", "null", "-"], cwd=work, check=True, capture_output=True, text=True)
        counts = re.findall(r"(?m)^frame=(\d+)", verified.stdout)
        if not counts or int(counts[-1]) != total_frames:
            raise ValueError("El archivo tiene menos o más fotogramas que la escaleta. Comprueba la duración de los clips.")
        publicar_archivo(work / "final.mp4", output)
    return {"archivo": str(output), "ancho": W, "alto": H, "fps": FPS, "fotogramas": total_frames, "segundos": total_frames / FPS}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("escaleta", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--ffmpeg", default=os.environ.get("MARKETINGIA_FFMPEG") or shutil.which("ffmpeg"))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.exit(1, "Instala FFmpeg o configura MARKETINGIA_FFMPEG.\n")
    print(json.dumps(render(args.escaleta, args.salida, args.ffmpeg), ensure_ascii=False))
