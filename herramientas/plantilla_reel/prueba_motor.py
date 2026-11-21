"""Prueba de integración con señales sintéticas y una campaña temporal sin material de clientes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
TOOLS = ("ElevenLabs","Whisper","invideo","HyperFrames","Remotion","gbro-collage-broll","ClaudeAnimationBase")

def escribir(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf8")

def huella(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default=os.getenv("REEL_FFMPEG","ffmpeg"))
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    def ff(*argv):
        subprocess.run([args.ffmpeg,"-v","error","-y",*map(str,argv)],check=True)
    with tempfile.TemporaryDirectory(prefix="prueba-reel-") as temp:
        camp=Path(temp)
        edit=camp/"edicion-07"
        fuente=camp/"material"; fuente.mkdir()
        guion=camp/"guion"; guion.mkdir()
        pistas=edit/"pistas"; pistas.mkdir(parents=True)
        dur=2.4
        ff("-f","lavfi","-i","testsrc2=size=256x456:rate=30","-t",dur,"-c:v","libx264","-pix_fmt","yuv420p",fuente/"camara.mp4")
        ff("-f","lavfi","-i","color=c=green:s=128x64","-frames:v","1","-threads","1",fuente/"firma.png")
        ff("-f","lavfi","-i","anullsrc=r=48000:cl=stereo","-t",dur,"-c:a","pcm_s16le",pistas/"voz.wav")
        ff("-f","lavfi","-i","sine=frequency=220:sample_rate=48000","-t",dur,"-ac","2",fuente/"ambiente.wav")
        tinta=fuente/"tinta";tinta.mkdir()
        ff("-f","lavfi","-i","color=c=yellow@0.35:s=32x32,format=rgba","-frames:v","24","-threads","1","-start_number","0",tinta/"s%02d.png")
        frase={"id":"f1","texto":"Una forma cambia.","objetivo_visual":"Seguir una forma durante el cambio."}
        script=guion/"voz-reel-07.json"; escribir(script,{"frases":[frase]})
        rel_srt="edicion-07/subtitulos.srt"
        (camp/rel_srt).write_text("1\n00:00:00,100 --> 00:00:02,000\nUna forma cambia.\n",encoding="utf8")
        config={"ambiente":"material/ambiente.wav","papel":"material/camara.mp4","tinta":"material/tinta"}
        escribir(edit/"recursos.json",config)
        voz_hash=huella(pistas/"voz.wav"); guion_hash=huella(script)
        escribir(edit/"alineacion.json",{"guion_sha256":guion_hash,"voz_sha256":voz_hash,"fotogramas":72})
        ordenes=[dict(id=f"orden-{n}",entrada=0,salida=dur,herramienta=tool,instruccion="Comprobar el contrato de prueba.",
                      insumo="Fijación sintética local.",resultado="Etapa validada.") for n,tool in enumerate(TOOLS,1)]
        cortes=[("material/camara.mp4",0,.8,"hyperframes"),("material/camara.mp4",.8,1.6,None),("material/firma.png",1.6,2.4,"placa")]
        tomas=[]
        for archivo,inicio,fin,efecto in cortes:
            toma=dict(frase="f1",archivo=archivo,desde=0,hasta=.8,entrada=inicio,salida=fin,motivo="Debe cubrir el intervalo de prueba.")
            if efecto: toma["tratamiento"]=efecto
            tomas.append(toma)
        plan={"duracion":dur,"ordenes":ordenes,"guion_voz":{"guion_sha256":guion_hash,"voz_sha256":voz_hash,"voz":"edicion-07/pistas/voz.wav","subtitulos":rel_srt,"tomas":tomas},
              "acento_tinta":{"frame":24,"x":300,"y":300,"ancho":120,"alto":120,"opacidad":0.4,"giro":0}}
        path=guion/"montaje-reel-07.json"; escribir(path,plan)
        base=[sys.executable,"-B",str(HERE/"motor.py")]
        opts=[str(camp),"--revision","7","--ffmpeg",args.ffmpeg]
        subprocess.run([*base,"validar",*opts],check=True,stdout=subprocess.DEVNULL)
        # Comprueba que un intervalo roto detenga la edición antes de renderizar.
        tomas[1]["entrada"]=.9; escribir(path,plan)
        failed=subprocess.run([*base,"validar",*opts],capture_output=True)
        if failed.returncode==0 or b"hueco" not in failed.stderr:
            raise AssertionError("El motor no detectó el hueco de la prueba.")
        tomas[1]["entrada"]=.8; escribir(path,plan)
        if args.render:
            master=camp/"salida.mp4"
            subprocess.run([*base,"render",*opts,"--salida",master],check=True)
            for name in ["imagen.mp4","voz.wav","ambiente.wav","subtitulos.srt"]:
                assert (pistas/name).stat().st_size>0
            # Un MP4 truncado o sin audio falla aunque exista en disco.
            ff("-xerror","-i",master,"-map","0:v:0","-map","0:a:0","-f","null","-")
            assert (edit/"fuentes/hyperframes-01/index.html").is_file()
        print("OK · continuidad, orden y huellas" + ("; máster, tres pistas y subtítulos verificados" if args.render else ""))

if __name__=="__main__":
    main()
