"""Memoria por cuenta. Los eventos versionados son la fuente y el Markdown es una vista reconstruible."""
from collections import defaultdict
from contextlib import closing
import datetime as dt
import json
import math
import os
from pathlib import Path
import sqlite3
from statistics import median
import tempfile
from html import escape

from campana import account_name
from instagram import numeric

FORMATOS = ("reel", "carrusel")
CLASES = ("instruccion", "decision", "vinculo", "etiquetas", "muestra")
METRICAS = ("vistas", "me_gusta", "comentarios", "guardados", "alcance", "compartidos")
VENTANAS = {24: (18, 30), 72: (60, 84), 168: (144, 192)}
PESOS = {"vistas": .45, "me_gusta": .20, "comentarios": .15, "guardados": .20}
UTC = dt.timezone.utc


def instante(valor):
    if not isinstance(valor, str):
        raise ValueError("Indica una fecha ISO 8601 con zona horaria.")
    when = dt.datetime.fromisoformat(valor)
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("La fecha requiere zona horaria.")
    return when.astimezone(UTC)


def ahora():
    return dt.datetime.now(UTC)


def texto(valor, nombre, limite=500):
    if not isinstance(valor, str) or not valor.strip() or len(valor) > limite:
        raise ValueError(f"Se requiere {nombre}, de hasta {limite} caracteres.")
    return valor.strip()


def formato(valor):
    if valor not in FORMATOS:
        raise ValueError("El formato debe ser reel o carrusel.")
    return valor


def rasgos(valores):
    if not isinstance(valores, list) or len(valores) > 32:
        raise ValueError("rasgos debe ser una lista de hasta 32 descriptores observables.")
    return sorted({texto(x, "rasgo", 100).casefold() for x in valores})


def abrir(raiz, cuenta):
    cuenta = account_name(cuenta)
    carpeta = Path(raiz) / "memoria" / cuenta
    carpeta.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(carpeta / "aprendizaje.sqlite", timeout=30, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS eventos (
        tipo TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, registrado TEXT NOT NULL,
        activo INTEGER NOT NULL, contenido TEXT NOT NULL, PRIMARY KEY(tipo,id,revision))""")
    return carpeta, db


def normalizar(db, evento, cuenta):
    if not isinstance(evento, dict):
        raise ValueError("Cada evento debe ser un objeto JSON.")
    if "cuenta" in evento and account_name(evento["cuenta"]) != cuenta:
        raise ValueError("La cuenta del evento difiere de su memoria.")
    clase = evento.get("tipo")
    retirada = clase == "retirar"
    if retirada:
        clase = evento.get("clase")
    if clase not in CLASES:
        raise ValueError("Tipo de evento desconocido.")
    if clase == "muestra" and not retirada:
        medio = numeric(evento.get("medio", ""))
        observada = instante(evento.get("observado"))
        clave = medio + "/" + observada.isoformat()
    else:
        clave = texto(evento.get("id"), "id", 250)
    prev = db.execute("SELECT * FROM eventos WHERE tipo=? AND id=? ORDER BY revision DESC LIMIT 1",
                      (clase, clave)).fetchone()
    anterior = json.loads(prev["contenido"]) if prev else {}
    activo = not retirada
    if retirada:
        if not prev:
            raise ValueError("No existe ese evento para retirarlo.")
        data = {"tipo": clase, "id": clave, "motivo_retiro": texto(evento.get("motivo"), "motivo de retiro")}
    else:
        data = {"tipo": clase, "id": clave}
        if clase in ("instruccion","decision"):
            fecha = evento.get("fecha") or anterior.get("fecha") or ahora().isoformat()
            data["fecha"] = instante(fecha).isoformat()
        if clase == "instruccion":
            data["directriz"] = texto(evento.get("directriz"), "directriz", 3000)
            data["fuente"] = texto(evento.get("fuente"), "fuente", 500)
            scope = evento.get("formato", "todos")
            data["formato"] = scope if scope == "todos" else formato(scope)
        elif clase == "decision":
            data["formato"] = formato(evento.get("formato"))
            opts = evento.get("opciones")
            if not isinstance(opts, list) or not 1 <= len(opts) <= 100:
                raise ValueError("Incluye entre 1 y 100 opciones efectivamente presentadas.")
            parsed = []
            for op in opts:
                if not isinstance(op, dict):
                    raise ValueError("Cada opción debe ser un objeto.")
                opt = {"id": texto(op.get("id"), "id de opción", 200), "formato": formato(op.get("formato", data["formato"])),
                       "rasgos": rasgos(op.get("rasgos", []))}
                for key in ("titulo", "huella_publicacion"):
                    if op.get(key):
                        opt[key] = texto(op[key], key, 800)
                parsed.append(opt)
            ids = {op["id"] for op in parsed}
            elegida = texto(evento.get("elegida"), "opción elegida", 200)
            if len(ids) != len(parsed) or elegida not in ids:
                raise ValueError("La elección debe identificar una de las opciones únicas.")
            if next(op for op in parsed if op["id"] == elegida)["formato"] != data["formato"]:
                raise ValueError("El formato de la decisión debe coincidir con la elegida.")
            data.update(opciones=sorted(parsed,key=lambda o:o["id"]), elegida=elegida)
            if evento.get("motivo_admin"):
                data["motivo_admin"] = texto(evento["motivo_admin"], "motivo del administrador", 2000)
        elif clase == "vinculo":
            numeric(clave)
            dec = texto(evento.get("decision"), "id de decisión", 250)
            cand = texto(evento.get("candidata"), "id de candidata", 200)
            # Una repetición conserva la evidencia original aunque el admin haya actualizado después sus opciones.
            if prev and prev["activo"] and anterior.get("decision") == dec and anterior.get("candidata") == cand:
                data = anterior
            else:
                decision = db.execute("SELECT * FROM eventos WHERE tipo='decision' AND id=? ORDER BY revision DESC LIMIT 1",(dec,)).fetchone()
                if not decision or not decision["activo"]:
                    raise ValueError("El vínculo requiere una decisión vigente.")
                registro = json.loads(decision["contenido"])
                if registro["elegida"] != cand:
                    raise ValueError("La candidata publicada difiere de la elección registrada.")
                op = next(op for op in registro["opciones"] if op["id"] == cand)
                data.update(decision=dec, candidata=cand, revision_decision=decision["revision"],
                            formato=op["formato"], rasgos=op["rasgos"])
        elif clase == "etiquetas":
            numeric(clave)
            data.update(formato=formato(evento.get("formato")), rasgos=rasgos(evento.get("rasgos", [])),
                        fuente=texto(evento.get("fuente"), "fuente de los rasgos observados", 500))
        elif clase == "muestra":
            publicada = instante(evento.get("publicado"))
            if publicada > observada:
                raise ValueError("La observación precede a la publicación.")
            m = evento.get("metricas")
            if not isinstance(m, dict) or set(m) - set(METRICAS):
                raise ValueError("Métricas admitidas: " + ", ".join(METRICAS))
            medidas = {}
            for k, v in m.items():
                if v is None:
                    continue
                if type(v) is not int or v < 0:
                    raise ValueError("Las métricas disponibles deben ser enteros no negativos.")
                medidas[k] = v
            data.update(medio=medio, formato=formato(evento.get("formato")), publicado=publicada.isoformat(),
                        observado=observada.isoformat(), metricas=medidas, fuente=texto(evento.get("fuente"), "fuente", 500))
            if evento.get("enlace"):
                data["enlace"] = texto(evento["enlace"], "permalink", 600)
    return clase, clave, prev, activo, data


def guardar(db, cuenta, evento, conservar_anteriores=()):
    clase, clave, prev, activo, data = normalizar(db, evento, cuenta)
    rev = prev["revision"] if prev else 0
    if prev and clase in conservar_anteriores:
        return {"tipo":clase, "id":clave, "revision":rev, "cambio":False}
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if prev and prev["activo"] == activo and prev["contenido"] == payload:
        return {"tipo":clase, "id":clave, "revision":rev, "cambio":False}
    esperado = evento.get("si_revision")
    if esperado is not None and (type(esperado) is not int or esperado != rev):
        raise ValueError(f"Conflicto de revisión. La versión actual de {clave} es {rev}.")
    db.execute("INSERT INTO eventos VALUES(?,?,?,?,?,?)",
               (clase,clave,rev+1,ahora().isoformat(),activo,payload))
    return {"tipo":clase, "id":clave, "revision":rev+1, "cambio":True}


def vigentes(db):
    rows = db.execute("""SELECT e.contenido FROM eventos e JOIN
        (SELECT tipo,id,MAX(revision) AS ultima FROM eventos GROUP BY tipo,id) u
        ON e.tipo=u.tipo AND e.id=u.id AND e.revision=u.ultima WHERE e.activo=1 ORDER BY e.tipo,e.id""")
    result = {tipo:[] for tipo in CLASES}
    for row in rows:
        data = json.loads(row[0])
        result[data["tipo"]].append(data)
    return result


def registrar_lote(raiz, cuenta, eventos, *, conservar_anteriores=()):
    cuenta = account_name(cuenta)
    carpeta, db = abrir(raiz,cuenta)
    with closing(db):
        db.execute("BEGIN IMMEDIATE")
        with db:
            recibos = [guardar(db,cuenta,e,conservar_anteriores) for e in eventos]
        materializar(carpeta, db, cuenta)
    return recibos


def registrar(raiz, cuenta, evento):
    return registrar_lote(raiz, cuenta, [evento])[0]


def historial(raiz, cuenta, clase, clave):
    _, db = abrir(raiz,cuenta)
    with closing(db):
        return [{"revision":r["revision"], "registrado":r["registrado"],"activo":bool(r["activo"]),
                 "evento":json.loads(r["contenido"])} for r in db.execute(
            "SELECT * FROM eventos WHERE tipo=? AND id=? ORDER BY revision", (clase,clave))]


def preferencias(decisiones):
    stats = defaultdict(list)
    for d in decisiones:
        opciones = [x for x in d["opciones"] if x["formato"] == d["formato"]]
        winner = next(x for x in opciones if x["id"] == d["elegida"])
        for tag in sorted({t for x in opciones for t in x["rasgos"]}):
            # Una alternativa sin etiquetas no equivale a ausencia comprobada de un rasgo.
            if any(not o["rasgos"] for o in opciones):
                continue
            frecuencia = sum(tag in x["rasgos"] for x in opciones)/len(opciones)
            if frecuencia < 1:
                stats[d["formato"],tag].append((tag in winner["rasgos"],frecuencia,d["id"]))
    pistas = []
    for (kind,tag), items in sorted(stats.items()):
        n = len(items)
        elegidos = sum(e[0] for e in items)
        exposicion = sum(e[1] for e in items)/n
        tendencia = elegidos/n - exposicion
        a_favor = elegidos >= 3 and tendencia >= .20
        en_contra = n-elegidos >= 3 and tendencia <= -.20
        if n >= 3 and (a_favor or en_contra):
            pistas.append({"formato":kind,"rasgo":tag,"elecciones":elegidos,"comparaciones":n,
                           "direccion":"favorecido" if a_favor else "menos_elegido",
                           "fraccion_ofrecida":round(exposicion,3),"evidencia":[e[2] for e in items]})
    return pistas


def contrastar(decision):
    """Diferencias descriptivas entre las opciones mostradas, incluso en la primera ronda."""
    elegida=next(o for o in decision["opciones"] if o["id"]==decision["elegida"])
    otras=sorted((o for o in decision["opciones"] if o["id"]!=elegida["id"]),
                 key=lambda o:(o["formato"]!=elegida["formato"],o["id"]))
    pares=[]
    variable=None
    for otra in otras[:3]:
        a,b=set(elegida["rasgos"]),set(otra["rasgos"])
        observable=bool(a and b)
        solo_a=sorted(a-b) if observable else []
        solo_b=sorted(b-a) if observable else []
        pares.append({"id":otra["id"],"titulo":otra.get("titulo",otra["id"]),"formato":otra["formato"],
                      "rasgos_comparables":observable,"solo_elegida":solo_a,"solo_alternativa":solo_b,
                      "comunes":sorted(a&b)})
        if variable is None and (solo_a or solo_b):
            variable=(solo_a or solo_b)[0]
    if variable:
        prueba=f"¿Cambia la elección al variar únicamente «{variable}» entre dos versiones del mismo formato?"
    elif any(o["formato"]!=elegida["formato"] for o in otras):
        prueba="¿Cambia la elección al presentar el mismo mensaje como reel y carrusel?"
    else:
        prueba=None
    return {"decision":decision["id"],"alternativas":pares,"total_alternativas":len(otras),"prueba":prueba}


def senales(actual, previos):
    med = actual["metricas"]
    detalles = {}
    for key,peso in PESOS.items():
        if key not in med:
            continue
        usar_tasa = key != "vistas" and med.get("alcance",0) >= 30
        def valor(m):
            return m[key]*1000/m["alcance"] if usar_tasa else m[key]
        candidatos = [p["metricas"] for p in previos if key in p["metricas"]
                      and (not usar_tasa or p["metricas"].get("alcance",0) >= 30)]
        candidatos = candidatos[-12:]
        if len(candidatos) < 5:
            continue
        base = median(valor(c) for c in candidatos)
        # Las medianas de un solo comentario/guardado o cero vistas son demasiado ruidosas.
        minimo = 20 if key == "vistas" else 2
        if base <= 0 or median(c[key] for c in candidatos) < minimo:
            continue
        ratio = valor(med)/base
        detalles[key] = {"valor":round(valor(med),3),"mediana":round(base,3),"n":len(candidatos),
                         "unidad":"por_1000_alcanzadas" if usar_tasa else "conteo",
                         "multiplo":round(ratio,3),"peso":peso}
    peso_total = sum(s["peso"] for s in detalles.values())
    if len(detalles)<2 or peso_total<.45:
        return detalles,None
    # Media geométrica ponderada, con contribuciones acotadas para un único pico de ruido.
    suma = sum(s["peso"]*math.log2(max(.25,min(4,s["multiplo"]))) for s in detalles.values())
    return detalles,round(2**(suma/peso_total),3)


def analizar_muestras(muestras, vinculos, fecha):
    limite = fecha - dt.timedelta(days=180)
    por_ventana = {}
    latest = {}
    for s in muestras:
        published, seen = instante(s["publicado"]), instante(s["observado"])
        if seen > fecha:
            continue
        mid = s["medio"]
        if mid not in latest or seen > instante(latest[mid]["observado"]):
            latest[mid]=s
        hours = (seen-published).total_seconds()/3600
        for target,(a,b) in VENTANAS.items():
            if a <= hours <= b:
                key=(s["formato"],target,mid)
                rank=(abs(hours-target),-len(s["metricas"]),s["observado"])
                if key not in por_ventana or rank < por_ventana[key][0]:
                    por_ventana[key]=(rank,s)
    resultados=[]
    por_grupo=defaultdict(list)
    for (kind,window,mid),(_,s) in por_ventana.items():
        por_grupo[kind,window].append(s)
    for (kind,window), filas in sorted(por_grupo.items()):
        filas.sort(key=lambda s:(s["publicado"],s["medio"]))
        for i,s in enumerate(filas):
            pub=instante(s["publicado"])
            if pub < limite:
                continue
            # La base solo contiene publicaciones previas y captura de edad equivalente disponible al observar.
            base=[p for p in filas[:i] if p["publicado"]<s["publicado"] and p["observado"]<=s["observado"]
                  and instante(p["publicado"]) >= pub-dt.timedelta(days=180)]
            detalle,score=senales(s,base)
            link=vinculos.get(s["medio"],{})
            tags=link.get("rasgos",[]) if link.get("formato")==kind else []
            resultados.append({"medio":s["medio"],"formato":kind,"publicado":s["publicado"],"ventana_h":window,
                "observado":s["observado"],"metricas":s["metricas"],"senales":detalle,"indice":score,"rasgos":tags,
                "estado":"sin_base" if score is None else ("alto" if score>=1.25 else "bajo" if score<=.8 else "habitual")})
    # Cada post aporta una vez por hipótesis; se prefiere 72 h y luego siete días.
    elegibles={}
    for r in sorted(resultados,key=lambda r:{72:0,168:1,24:2}[r["ventana_h"]]):
        if r["indice"] is not None:
            elegibles.setdefault(r["medio"],r)
    por_rasgo=defaultdict(list)
    for r in elegibles.values():
        for tag in r["rasgos"]:
            por_rasgo[r["formato"],r["ventana_h"],tag].append(r)
    pistas=[]
    for (kind,window,tag),rows in sorted(por_rasgo.items()):
        indices=[r["indice"] for r in rows]
        alta=sum(i>=1.25 for i in indices)
        baja=sum(i<=.8 for i in indices)
        if len(rows)>=3 and max(alta,baja)/len(rows)>=2/3 and (median(indices)>=1.25 or median(indices)<=.8):
            pistas.append({"formato":kind,"ventana_h":window,"rasgo":tag,"n":len(rows),
                          "direccion":"alto" if alta>baja else "bajo","mediana_indice":round(median(indices),3),
                          "medios":[r["medio"] for r in rows]})
    return sorted(latest.values(),key=lambda s:s["publicado"],reverse=True),resultados,pistas


def construir(db, cuenta, fecha):
    ev=vigentes(db)
    decisiones=sorted((d for d in ev["decision"] if instante(d["fecha"]) <= fecha),key=lambda d:d["fecha"],reverse=True)
    recientes=[d for d in decisiones if instante(d["fecha"])>=fecha-dt.timedelta(days=90)]
    mandatos=[d for d in ev["instruccion"] if instante(d["fecha"])<=fecha]
    # Las etiquetas verificadas directamente sobre el post pueden corregir la propuesta original.
    links={v["id"]:v for v in ev["vinculo"]+ev["etiquetas"]}
    ultimas,comparaciones,hipotesis=analizar_muestras(ev["muestra"],links,fecha)
    return {"cuenta":cuenta, "instrucciones":mandatos, "decisiones":decisiones,
            "contrastes_decisiones":[contrastar(d) for d in decisiones],
            "preferencias_inferidas":preferencias(recientes), "publicaciones":ultimas,
            "comparaciones":comparaciones, "hipotesis_rendimiento":hipotesis,
            "medios_sin_etiquetar":[s["medio"] for s in ultimas if not links.get(s["medio"],{}).get("rasgos")]}


def legible(value):
    # El contenido externo se presenta en una sola línea, como cita de datos.
    s=escape(" ".join(str(value).split()),quote=False)
    for signo in ("\\","*","_","`","[","]","#","|",">"):
        s=s.replace(signo,"\\"+signo)
    return s


def markdown(r):
    l=["# Memoria de @"+r["cuenta"],"", "## Instrucciones explícitas del usuario",""]
    l.extend(f"- [{d['formato']}] {legible(d['directriz'])} · Fuente {legible(d['fuente'])} · ID {legible(d['id'])}" for d in r["instrucciones"])
    if not r["instrucciones"]:
        l.append("Sin instrucciones registradas.")
    l+=["","## Selecciones y motivos del administrador",""]
    for d,contraste in zip(r["decisiones"][:12],r["contrastes_decisiones"][:12]):
        op=next(o for o in d["opciones"] if o["id"]==d["elegida"])
        motivo="Motivo declarado «"+legible(d["motivo_admin"])+"»." if d.get("motivo_admin") else "Motivo sin declarar."
        l.append(f"- {d['fecha'][:10]} · {d['formato']} · {legible(op.get('titulo',op['id']))} ({legible(op['id'])}). {motivo} Conjunto {legible(d['id'])}.")
        for par in contraste["alternativas"]:
            nombre=legible(par["titulo"])+" ("+legible(par["id"])+", "+par["formato"]+")"
            descripciones=[]
            if par["formato"]!=op["formato"]:
                descripciones.append(f"el formato cambia de {op['formato']} a {par['formato']}")
            if par["rasgos_comparables"]:
                for campo,etiqueta in (("solo_elegida","solo etiquetado en la elegida"),("solo_alternativa","solo etiquetado en la alternativa"),("comunes","etiquetado en ambas")):
                    if par[campo]:
                        descripciones.append(etiqueta+" «"+"», «".join(legible(x) for x in par[campo])+"»")
            else:
                descripciones.append("faltan etiquetas para comparar los rasgos visuales o de contenido")
            l.append("  - Alternativa "+nombre+". "+". ".join(descripciones)+".")
        if contraste["total_alternativas"]>3:
            l.append("  - Las demás alternativas están en el resumen JSON de esta ronda.")
        if contraste["prueba"]:
            l.append("  - Hipótesis para otra ronda. "+legible(contraste["prueba"])+
                     " Aplicar las instrucciones vigentes y mantener constantes los demás rasgos y el objetivo del brief.")
        elif contraste["alternativas"]:
            l.append("  - Para probar una explicación, primero documentar una diferencia observable entre las opciones.")
    if not r["decisiones"]:
        l.append("Todavía no hay elecciones del administrador.")
    l+=["","## Preferencias inferidas de elecciones",""]
    for p in r["preferencias_inferidas"]:
        direccion = "favorecido" if p["direccion"]=="favorecido" else "menos elegido"
        l.append(f"- {p['formato']} · «{legible(p['rasgo'])}» ({direccion}) aparece en {p['elecciones']}/{p['comparaciones']} opciones elegidas. Presencia media en alternativas {p['fraccion_ofrecida']:.0%}. Contrastar en otra propuesta.")
    if not r["preferencias_inferidas"]:
        l.append("Muestra insuficiente para inferir una preferencia.")
    l+=["","## Resultados observados en Instagram",""]
    labels={"vistas":"vistas","me_gusta":"me gusta","comentarios":"comentarios","guardados":"guardados","alcance":"alcance","compartidos":"compartidos"}
    for s in r["publicaciones"][:12]:
        valores=", ".join(f"{labels[k]} {s['metricas'].get(k,'s/d')}" for k in METRICAS)
        l.append(f"- {s['formato']} {s['medio']} · publicado {s['publicado'][:10]} · observado {s['observado'][:10]} · {valores}. Fuente {legible(s['fuente'])}.")
    if not r["publicaciones"]:
        l.append("Sin métricas de publicaciones propias registradas.")
    l+=["","## Comparación con el historial de la cuenta",""]
    ran=sorted((x for x in r["comparaciones"] if x["indice"] is not None),key=lambda x:x["publicado"],reverse=True)
    for x in ran[:12]:
        l.append(f"- {x['formato']} {x['medio']} · {x['ventana_h']} h · índice {x['indice']:.2f}× ({x['estado']}). "
                 +", ".join(f"{labels[k]} {s['multiplo']:.2f}×, n={s['n']}" for k,s in x["senales"].items())+".")
    if not ran:
        l.append("Todavía no hay muestras suficientes del mismo formato y edad para calcular un índice.")
    l+=["","## Hipótesis para la próxima prueba",""]
    for p in r["hipotesis_rendimiento"]:
        l.append(f"- {p['formato']} · {p['ventana_h']} h · «{legible(p['rasgo'])}» se asoció con rendimiento {p['direccion']} en el grupo de {p['n']} publicaciones, mediana {p['mediana_indice']:.2f}×. IDs {', '.join(p['medios'])}. Contrastar cambiando un solo rasgo.")
    if not r["hipotesis_rendimiento"]:
        l.append("No se ha repetido una asociación con evidencia suficiente para orientar la siguiente prueba.")
    l+=["",f"Publicaciones sin etiquetas vinculadas: {len(r['medios_sin_etiquetar'])}. Sus cifras pueden alimentar la referencia del formato.","",
        "Las elecciones son de los últimos 90 días para inferir gustos; las instrucciones explícitas siguen vigentes hasta corregirse o retirarse. Las comparaciones usan publicaciones previas de hasta 180 días y las ventanas de 24, 72 o 168 h. Un índice expresa una asociación. Consultar APRENDIZAJE.md para los umbrales y el historial de versiones en la base de esta cuenta."]
    return "\n".join(l)+"\n"


def materializar(carpeta, db, cuenta):
    # El bloqueo serializa también la proyección del archivo; una caída después de un commit
    # se recupera volviendo a ejecutar resumen sobre el registro confirmado.
    db.execute("BEGIN IMMEDIATE")
    with db:
        datos = construir(db,cuenta,ahora())
        destino = carpeta/"MEMORIA.md"
        content = markdown(datos)
        if destino.exists() and destino.read_text(encoding="utf8") == content:
            return datos
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf8",dir=carpeta,delete=False) as f:
                temp=Path(f.name)
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp,destino)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        return datos


def resumen(raiz, cuenta):
    cuenta=account_name(cuenta)
    carpeta,db=abrir(raiz,cuenta)
    with closing(db):
        return materializar(carpeta,db,cuenta)
