"""Muestreo local de la primera pista de audio. Usa solo la biblioteca estándar salvo el worker de Whisper."""
from array import array
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile

FRECUENCIA = 16000
DEFAULTS = {"ventanas": 3, "segundos_por_ventana": 7, "timeout_ffmpeg": 15,
            "timeout_whisper": 65, "habilitar_whisper": False, "idioma": "es"}


def configuracion(raiz):
    path = raiz / ".local/biblioteca-audio.json"
    cfg = dict(DEFAULTS)
    if not path.exists():
        return cfg, None
    try:
        origen = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(origen, dict):
            raise ValueError("se esperaba un objeto")
        cfg.update(origen)
        for key, minimo, maximo in (("ventanas", 1, 3), ("segundos_por_ventana", 2, 12),
                                    ("timeout_ffmpeg", 3, 30), ("timeout_whisper", 5, 90)):
            if type(cfg[key]) is not int or not minimo <= cfg[key] <= maximo:
                raise ValueError(f"{key} debe estar entre {minimo} y {maximo}")
        if type(cfg["habilitar_whisper"]) is not bool or not re.fullmatch("[a-z]{2,3}", cfg["idioma"]):
            raise ValueError("revisa habilitar_whisper e idioma")
        if any(k in cfg and not isinstance(cfg[k],str) for k in ("python_whisper","modelo_whisper")):
            raise ValueError("las rutas locales de Whisper deben ser texto")
        return cfg, None
    except (OSError, ValueError, TypeError) as error:
        return dict(DEFAULTS), f"Configuración local no utilizable ({error}). Se aplicó el muestreo básico."


def actividad(pcm):
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(map(abs, samples), default=0)
    energies = []
    compatible = 0
    for inicio in range(0, len(samples), 800):
        block = samples[inicio:inicio+800]
        if len(block) < 320:
            continue
        rms = math.sqrt(sum(s*s for s in block)/len(block))
        energies.append(rms)
        crossings = sum((a < 0) != (b < 0) for a,b in zip(block,block[1:])) / len(block)
        if rms >= 80 and .008 <= crossings <= .35:
            compatible += 1
    db = round(20*math.log10(peak/32768),1) if peak else None
    # La modulación y los cruces por cero solo priorizan muestras para ASR; música también puede cumplirlos.
    if len(energies)<4 or not peak:
        return db, 0
    mean = statistics.fmean(energies)
    modulation = statistics.pstdev(energies)/max(mean,1)
    score = compatible/len(energies)*min(1,modulation*3)
    return db, round(score,3)


def analizar_audio(raiz, archivo, tecnica, *, ffmpeg="ffmpeg"):
    """Devuelve estado, resumen, ventanas y transcripción orientativa; un fallo no detiene el análisis visual."""
    raiz = Path(raiz)
    out = {"estado":"no_verificado","resumen":"","ventanas":[],"transcripcion":None,"whisper":"omitido","avisos":[]}
    if not isinstance(tecnica,dict) or not isinstance(tecnica.get("audio"),list):
        out["resumen"]="La inspección técnica no confirmó las pistas de audio."
        return out
    if not tecnica["audio"]:
        out.update(estado="sin_pista",resumen="FFprobe no encontró pistas de audio.")
        return out
    cfg, aviso = configuracion(raiz)
    if aviso:
        out["avisos"].append(aviso)
    try:
        dur = float(tecnica.get("duracion"))
        if not math.isfinite(dur) or dur <= 0:
            raise ValueError("duración inválida")
    except (TypeError,ValueError):
        out["resumen"]="Hay pista de audio, pero falta una duración válida para muestrearla."
        return out
    seconds = min(cfg["segundos_por_ventana"],dur)
    n = min(cfg["ventanas"],max(1,math.floor(dur/seconds)))
    candidatos = []
    for i in range(n):
        start = round((dur-seconds)*i/max(n-1,1),3)
        command = [str(ffmpeg),"-hide_banner","-loglevel","error","-nostdin","-ss",str(start),"-i",str(archivo),
                   "-map","0:a:0","-t",str(seconds),"-vn","-sn","-dn","-ac","1","-ar",str(FRECUENCIA),
                   "-c:a","pcm_s16le","-f","s16le","pipe:1"]
        try:
            proc = subprocess.run(command,capture_output=True,timeout=cfg["timeout_ffmpeg"])
            pcm = proc.stdout
            if proc.returncode or len(pcm)<2 or len(pcm)%2:
                raise ValueError("FFmpeg no entregó muestras PCM")
        except (subprocess.TimeoutExpired,OSError,ValueError) as exc:
            out["avisos"].append(f"Ventana desde {start:.2f} s sin verificar ({type(exc).__name__}).")
            continue
        peak, score = actividad(pcm)
        win = {"inicio":start,"fin":round(min(dur,start+len(pcm)/(2*FRECUENCIA)),3),
               "pico_dbfs":peak,"silencio_digital":peak is None}
        out["ventanas"].append(win)
        if score>=.12:
            candidatos.append((score,len(out["ventanas"])-1,pcm))
    if not out["ventanas"]:
        out["resumen"]="Hay una pista de audio. FFmpeg no pudo comprobar las ventanas solicitadas."
        return out
    horas = ", ".join(f"{w['inicio']:.2f}–{w['fin']:.2f} s" for w in out["ventanas"])
    signal = any(not w["silencio_digital"] for w in out["ventanas"])
    out["estado"] = "senal_presente" if signal else "silencio_muestreado"
    if not signal:
        out["resumen"]="Silencio digital en las muestras de la primera pista ("+horas+"). La observación solo cubre esos tramos."
        return out
    out["resumen"]="Se detectó señal en la primera pista. Tramos comprobados: "+horas+"."
    if not candidatos:
        out["whisper"]="sin_voz_probable"
        out["resumen"]+=" El muestreo no encontró un tramo claro para transcribir."
        return out
    if not cfg["habilitar_whisper"]:
        out["whisper"]="desactivado"
        return out
    python = raiz / (cfg.get("python_whisper") or "")
    modelo = raiz / (cfg.get("modelo_whisper") or "")
    if not python.is_file() or not modelo.is_file():
        out["whisper"]="no_disponible"
        out["resumen"]+=" Whisper local no está disponible."
        return out
    try:
        with tempfile.TemporaryDirectory(prefix="biblioteca-audio-") as tmp:
            # Dos candidatas como máximo, un único proceso y un único presupuesto de tiempo por archivo.
            mejores=sorted(candidatos,key=lambda c:c[0],reverse=True)[:2]
            rutas=[]
            for _,idx,pcm in mejores:
                ruta=Path(tmp)/f"{idx}.pcm"
                ruta.write_bytes(pcm)
                rutas.append(str(ruta))
            cmd=[str(python),"-B",str(Path(__file__).resolve()),"--whisper",str(modelo.resolve()),cfg["idioma"],*rutas]
            child=subprocess.run(cmd,capture_output=True,timeout=cfg["timeout_whisper"])
            if child.returncode:
                raise ValueError("el entorno local no pudo transcribir")
            data=json.loads(child.stdout.decode("utf8"))
        if data:
            win=out["ventanas"][data["indice"]]
            txt=" ".join(data["texto"].split())[:500]
            out["transcripcion"]={"inicio":win["inicio"],"fin":win["fin"],"texto":txt,"orientativa":True}
            out["whisper"]="transcrito"
            out["resumen"]+=f" Transcripción orientativa ({win['inicio']:.2f}–{win['fin']:.2f} s): «{txt}»."
        else:
            out["whisper"]="no_concluyente"
            out["resumen"]+=" Whisper no devolvió una frase suficientemente clara en los tramos analizados."
    except (OSError,ValueError,KeyError,IndexError,TypeError,subprocess.TimeoutExpired) as exc:
        out["whisper"]="tiempo_agotado" if isinstance(exc,subprocess.TimeoutExpired) else "no_disponible"
        out["avisos"].append("No se completó el reconocimiento local: "+type(exc).__name__+".")
        out["resumen"]+=" La transcripción local quedó sin verificar."
    return out


def reconocer(modelo,idioma,rutas):
    import numpy as np
    import torch
    import whisper
    torch.set_num_threads(3)
    model=whisper.load_model(str(modelo),device="cpu")
    for raw in rutas:
        ruta=Path(raw)
        pcm=np.frombuffer(ruta.read_bytes(),dtype="<i2").astype(np.float32)/32768
        result=model.transcribe(pcm,language=idioma,fp16=False,verbose=None,temperature=0,
                                condition_on_previous_text=False)
        segmentos=[s["text"].strip() for s in result.get("segments",[])
                   if s.get("no_speech_prob",1)<.55 and s.get("avg_logprob",-10)>-1.0
                   and s.get("compression_ratio",10)<2.2]
        text=" ".join(segmentos)
        tokens=re.findall(r"\w+",text.casefold())
        # Descartar bucles frecuentes de Whisper ante música o efectos.
        pares=list(zip(tokens,tokens[1:]))
        if len(tokens)>=3 and len(set(tokens))>=3 and len(set(pares))>=max(1,len(pares)*.6):
            return {"indice":int(ruta.stem),"texto":text}
    return None


if __name__=="__main__" and sys.argv[1:2]==["--whisper"]:
    result=reconocer(Path(sys.argv[2]),sys.argv[3],sys.argv[4:])
    sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False).encode("utf8"))
