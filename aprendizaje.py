"""CLI de memoria editorial y captura de métricas de Instagram. Solo efectúa lecturas remotas."""
import argparse
from contextlib import closing
from itertools import islice
import json
from pathlib import Path
import sqlite3
import sys
import tomllib

from campana import ROOT, account_name
from herramientas.aprendizaje import (CLASES, abrir, ahora, historial, instante, registrar,
                                     registrar_lote, resumen, vigentes)
from instagram import MEDIA_FIELDS, Meta, numeric, supported


def lectura(path, consulta, params=()):
    if not path.is_file():
        return []
    with closing(sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True,timeout=10)) as db:
        return db.execute(consulta,params).fetchall()


def leer_insights(meta, medio, avisos):
    nombres={"views":"vistas","reach":"alcance","saved":"guardados","shares":"compartidos"}
    def consulta(keys):
        data=meta.api(medio+"/insights",{"metric":",".join(keys)})
        medidas={}
        for obj in data.get("data",[]):
            key=obj.get("name")
            if key not in nombres:
                continue
            values=obj.get("values") or []
            value=(values[-1] if values else obj.get("total_value",{})).get("value")
            if type(value) is int and value>=0:
                medidas[nombres[key]]=value
        return medidas
    try:
        return consulta(nombres)
    except ValueError as exc:
        # Por ejemplo, falta el token de insights. Las métricas públicas siguen siendo aprovechables.
        avisos.add(str(exc))
        return {}
    except RuntimeError as exc:
        avisos.add(f"{medio}: no se recibió el conjunto de insights. {exc}")
        # Algunos formatos o versiones de Graph ofrecen únicamente parte de los campos.
        individual={}
        for nombre in nombres:
            try:
                individual.update(consulta([nombre]))
            except (ValueError,RuntimeError,OSError) as error:
                avisos.add(f"{medio}/{nombre}: {error}")
        return individual
    except OSError as exc:
        avisos.add(f"{medio}: {exc}")
        return {}


def sincronizar(raiz, cuenta, meta=None, limite=30, solo_publicas=False):
    raiz=Path(raiz)
    cuenta=account_name(cuenta)
    if type(limite) is not int or not 1<=limite<=500:
        raise ValueError("El límite de captura debe estar entre 1 y 500 publicaciones.")
    with (raiz/"operacion.toml").open("rb") as f:
        config=tomllib.load(f)
    if account_name(config["cuenta"])!=cuenta:
        raise ValueError("La cuenta solicitada no coincide con el adaptador configurado.")
    meta=meta or Meta()
    identity=meta.identity(config)
    path=meta.account+"/media"
    rows=(meta.iter_rows(path,MEDIA_FIELDS,max_rows=500,page_size=min(limite,50))
          if hasattr(meta,"iter_rows") else islice(meta.pages(path,MEDIA_FIELDS),500))
    marca=ahora().isoformat()
    samples=[]
    avisos=set()
    own=[]
    ids=set()
    revisados=0
    for item in rows:
        revisados+=1
        if not supported(item):
            continue
        # La colección pertenece a la identidad comprobada; comprobar también la fila cuando lo declara.
        if item.get("username") and account_name(item["username"])!=cuenta:
            avisos.add("Se omitió un medio cuya cuenta no coincide con la identidad verificada.")
            continue
        try:
            published=instante(item.get("timestamp"))
            mid=numeric(item.get("id",""))
            if mid in ids:
                continue
            if published>instante(marca):
                raise ValueError("Fecha de publicación posterior a la observación.")
            own.append((published,mid,item))
            ids.add(mid)
            if len(own)>=limite:
                break
        except (ValueError,TypeError) as exc:
            avisos.add(f"Fila omitida: {exc}")
    for pub,mid,item in sorted(own,key=lambda e:(e[0],e[1]),reverse=True)[:limite]:
        met={}
        for src,dst in (("like_count","me_gusta"),("comments_count","comentarios")):
            n=item.get(src)
            if type(n) is int and n>=0:
                met[dst]=n
        if not solo_publicas:
            met.update(leer_insights(meta,mid,avisos))
        samples.append({"tipo":"muestra","medio":mid,"formato":"carrusel" if item.get("media_type")=="CAROUSEL_ALBUM" else "reel",
                        "publicado":pub.isoformat(),"observado":marca,"metricas":met,"enlace":item.get("permalink"),
                        "fuente":"Meta Graph API · @"+cuenta+" · "+mid})
    # No se asume que una pieza elegida se publicó por coincidencia de fecha.
    # El adaptador solo aporta vínculos si confirma su ID y la huella exacta del medio y su caption.
    _,db=abrir(raiz,cuenta)
    with closing(db):
        eventos=vigentes(db)
    hashes={}
    for d in eventos["decision"]:
        o=next(x for x in d["opciones"] if x["id"]==d["elegida"])
        if o.get("huella_publicacion"):
            hashes.setdefault(o["huella_publicacion"],[]).append((d["id"],o["id"],o["formato"]))
    existentes={v["id"] for v in eventos["vinculo"]}
    feed=lectura(raiz/"estado/acciones.sqlite",
                 "SELECT clave,huella,remoto FROM acciones WHERE estado='confirmado' AND remoto IS NOT NULL")
    formatos={s["medio"]:s["formato"] for s in samples}
    links=[]
    for clave,huella,remote in feed:
        parts=clave.split(":")
        if len(parts)!=3 or parts[0]!=identity["id"] or parts[1] not in ("reel","feed") or remote in existentes:
            continue
        matches=hashes.get(huella,[])
        if len(matches)==1 and matches[0][2]==formatos.get(remote):
            dec,cand,_=matches[0]
            links.append({"tipo":"vinculo","id":remote,"decision":dec,"candidata":cand})
    results=registrar_lote(raiz,cuenta,samples+links,conservar_anteriores=("vinculo","muestra"))
    return {"cuenta":cuenta,"capturas":len(samples),"medios_revisados":revisados,"vinculos_confirmados":sum(r["tipo"]=="vinculo" and r["cambio"] for r in results),
            "cambios":sum(r["cambio"] for r in results),"observado":marca,"avisos":sorted(avisos)}


def importar_radar(raiz, cuenta):
    raiz=Path(raiz)
    cuenta=account_name(cuenta)
    rows=lectura(raiz/"estado/radar.sqlite",
        "SELECT medio,publicado,observado,vistas,enlace FROM muestras WHERE cuenta=? COLLATE NOCASE",(cuenta,))
    events=[{"tipo":"muestra","medio":mid,"formato":"reel","publicado":pub,"observado":obs,
             "metricas":{"vistas":views},"enlace":enlace,"fuente":"radar.sqlite · muestras · @"+cuenta}
            for mid,pub,obs,views,enlace in rows]
    # Una captura histórica solo de vistas nunca sustituye una observación más completa en el mismo instante.
    receipts=registrar_lote(raiz,cuenta,events,conservar_anteriores=("muestra",))
    return {"cuenta":cuenta,"capturas_historicas":len(events),"incorporadas":sum(r["cambio"] for r in receipts)}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raiz",type=Path,default=ROOT)
    p.add_argument("--cuenta")
    sub=p.add_subparsers(dest="accion",required=True)
    add=sub.add_parser("registrar")
    add.add_argument("archivo",help="Ruta JSON o - para stdin; admite un evento o una lista.")
    sub.add_parser("resumen")
    sub.add_parser("importar-radar")
    hist=sub.add_parser("historial")
    hist.add_argument("clase",choices=CLASES)
    hist.add_argument("id")
    sync=sub.add_parser("sincronizar")
    sync.add_argument("--limite",type=int,default=30)
    sync.add_argument("--solo-publicas",action="store_true")
    args=p.parse_args(argv)
    if args.cuenta:
        cuenta=account_name(args.cuenta)
    else:
        with (args.raiz/"operacion.toml").open("rb") as f:
            cuenta=account_name(tomllib.load(f)["cuenta"])
    if args.accion=="registrar":
        evento=json.loads(sys.stdin.buffer.read().decode("utf-8-sig") if args.archivo=="-" else Path(args.archivo).read_text(encoding="utf-8-sig"))
        return registrar_lote(args.raiz,cuenta,evento) if isinstance(evento,list) else registrar(args.raiz,cuenta,evento)
    if args.accion=="historial":
        return historial(args.raiz,cuenta,args.clase,args.id)
    if args.accion=="sincronizar":
        return sincronizar(args.raiz,cuenta,limite=args.limite,solo_publicas=args.solo_publicas)
    if args.accion=="importar-radar":
        return importar_radar(args.raiz,cuenta)
    return resumen(args.raiz,cuenta)


if __name__=="__main__":
    try:
        print(json.dumps(main(),ensure_ascii=False,indent=2))
    except (OSError,RuntimeError,ValueError,TypeError,KeyError,sqlite3.Error) as error:
        sys.exit(str(error))
