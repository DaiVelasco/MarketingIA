"""Produce un reel desde una campaña existente y sus propios materiales."""
import argparse
from contextlib import contextmanager, nullcontext
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PLANTILLA = Path(__file__).resolve().parent
sys.path.insert(0, str(PLANTILLA.parents[1]))
from herramientas.edicion_reel import cargar, local, orden_montaje
from herramientas.entrega_archivos import publicar_archivo
from ambiente import PISTA_A2, capas

@contextmanager
def reservar_revision(carpeta):
    """El sistema operativo libera el bloqueo aunque un proceso termine inesperadamente."""
    carpeta.mkdir(parents=True,exist_ok=True)
    with (carpeta/".produccion.lock").open("a+b") as lock:
        lock.seek(0,2)
        if lock.tell()==0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name=="nt":
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("Otro proceso está produciendo esta revisión.") from exc
        yield

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="accion", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("campana", type=Path)
    common.add_argument("--revision", type=int, required=True)
    common.add_argument("--ffmpeg", default=os.getenv("REEL_FFMPEG","ffmpeg"))
    voz = commands.add_parser("voz", parents=[common], help="Prepara A1 y ejecuta Whisper antes de elegir tomas.")
    voz.add_argument("--original", required=True, help="Ruta relativa a la campaña del audio de ElevenLabs.")
    voz.add_argument("--modelo", type=Path, required=True, help="Archivo local de modelo de Whisper.")
    commands.add_parser("validar", parents=[common], help="Revisa guion, voz, SRT, fuentes y continuidad del montaje.")
    render = commands.add_parser("render", parents=[common], help="Renderiza insertos, pistas sueltas y máster.")
    render.add_argument("--salida", type=Path, help="Ruta nueva del MP4. Por defecto se usa la carpeta de terminados.")
    args = parser.parse_args()
    if args.revision < 1:
        parser.error("La revisión debe ser positiva.")
    camp = args.campana.resolve(strict=True)
    codigo = f"{args.revision:02}"
    edit = camp / f"edicion-{codigo}"
    with reservar_revision(edit) if args.accion!="validar" else nullcontext():
        ejecutar(args,parser,camp,codigo,edit)

def ejecutar(args,parser,camp,codigo,edit):
    ambiente = dict(os.environ, REEL_CAMPANA=str(camp), REEL_REVISION=str(args.revision), REEL_FFMPEG=args.ffmpeg)
    def etapa(nombre, *argumentos):
        subprocess.run([sys.executable,str(PLANTILLA/nombre),*map(str,argumentos)],env=ambiente,check=True)
    if args.accion=="voz":
        if (edit/"entrega-local.json").exists():
            raise ValueError("La revisión ya tiene una entrega. Guarda la locución nueva en otra revisión.")
        original=local(camp,args.original)
        modelo=args.modelo.resolve(strict=True)
        if not shutil.which(args.ffmpeg):
            parser.error("Indica una instalación válida de FFmpeg.")
        etapa("voz.py", original, modelo)
        return
    info=orden_montaje(camp,args.revision)
    orden=cargar(camp/"guion"/f"montaje-reel-{codigo}.json")
    recursos=cargar(edit/"recursos.json")
    capas_audio = capas(camp, recursos)
    info["capas_audio"] = ["voz", *capas_audio]
    if recursos.get("ambiente"):
        print("Se omite la pista ambiente declarada en recursos.json durante el montaje.", file=sys.stderr)
    anterior=0
    efectos=[]
    for n,toma in enumerate(orden["guion_voz"]["tomas"],1):
        ini,fin=round(toma["entrada"]*30),round(toma["salida"]*30)
        if ini!=anterior or fin<=ini:
            raise ValueError(f"Hay hueco, solapamiento o duración nula en la toma {n}.")
        anterior=fin
        if toma.get("tratamiento")=="hyperframes":
            local(camp,recursos.get("papel"))
            efectos.append(n)
    if anterior!=round(info["duracion"]*30):
        raise ValueError("Las tomas deben cubrir todos los fotogramas.")
    if orden.get("acento_tinta"):
        carpeta=recursos.get("tinta","")
        for n in range(24):
            local(camp,str(Path(carpeta)/f"s{n:02}.png"))
    if args.accion=="validar":
        print(json.dumps(info,ensure_ascii=False,indent=2))
        return
    if not shutil.which(args.ffmpeg) or not shutil.which("node"):
        parser.error("Para renderizar se requieren FFmpeg y Node.")
    destino=(args.salida or camp/"Videos del proyecto - Reel de Instagram/03 - Videos terminados"/f"{codigo} - Reel.mp4").resolve()
    if destino.exists():
        raise ValueError(f"Ya existe un archivo en el destino: {destino}")
    for n in efectos:
        etapa("detalle.py","--escena",n)
    etapa("componer.py","--salida",destino)
    publicar_archivo(local(camp,orden["guion_voz"]["subtitulos"]),edit/"pistas/subtitulos.srt")
    from herramientas.edicion_reel import sha256
    import tempfile
    pistas = {p.name:sha256(p) for p in (edit/"pistas").iterdir() if p.name in {"imagen.mp4","voz.wav",PISTA_A2,"subtitulos.srt"}}
    recibo = {"master":destino.name,"video_sha256":sha256(destino),"orden_sha256":info["orden_sha256"],"pistas":pistas,
              "capas_audio": info["capas_audio"]}
    with tempfile.TemporaryDirectory() as temporal:
        path=Path(temporal)/"entrega-local.json"
        path.write_text(json.dumps(recibo,ensure_ascii=False,indent=2),encoding="utf8")
        publicar_archivo(path,edit/"entrega-local.json")
    print(json.dumps({"master":str(destino),"pistas":str(edit/"pistas")},ensure_ascii=False))

if __name__=="__main__":
    try:
        main()
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        sys.exit(str(error))
