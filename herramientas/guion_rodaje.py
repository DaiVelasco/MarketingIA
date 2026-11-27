"""Hoja de rodaje previa a la voz. Los segundos son estimaciones de la narración."""
from datetime import date
import json
import math


INTENCIONES = ("cercano", "curioso", "sereno", "enérgico", "seguro")
BLOQUES = {"toma": ("quien", "accion", "fin"), "camara": ("posicion", "plano", "foco"),
           "edicion": ("entrada", "corte", "enlace")}


def requiere_rodaje(carpeta):
    try:
        jornada = date.fromisoformat(carpeta.name)
    except ValueError:
        return False
    return carpeta.parent.name == "konduce.ve" and jornada >= date(2026, 11, 27)


def texto(obj, campo, donde):
    valor = obj.get(campo) if isinstance(obj, dict) else None
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"Falta {campo} en {donde}.")
    return valor.strip()


def apertura(rodaje):
    escena = next(iter(rodaje.get("escenas") or []), {})
    toma = escena.get("toma") if isinstance(escena, dict) else None
    if isinstance(toma, dict):
        return " · ".join(str(toma.get(k, "")).strip() for k in ("quien", "accion"))
    return None


def historial(carpeta):
    """Última revisión de cada turno por jornada, incluidos títulos de formato anterior."""
    carpeta = carpeta.resolve()
    dias = sorted((p for p in carpeta.parent.iterdir() if p.is_dir() and p.name <= carpeta.name
                   and (p / "guion").is_dir()), reverse=True)
    filas = []
    for dia in dias[:7]:
        vistos = set()
        archivos = [p for p in (dia / "guion").glob("voz-reel-*.json") if p.stem.rsplit("-", 1)[1].isdigit()]
        for p in sorted(archivos, key=lambda p: int(p.stem.rsplit("-", 1)[1]), reverse=True):
            guion = json.loads(p.read_text(encoding="utf-8-sig"))
            rodaje = guion.get("rodaje") or {}
            titulo = guion.get("titulo") or p.stem
            turno = rodaje.get("turno")
            clave = ("turno", turno) if turno else ("titulo", titulo.casefold())
            if clave in vistos:
                continue
            vistos.add(clave)
            frase = next(iter(guion.get("frases") or []), {})
            filas.append(dict(fecha=dia.name, turno=turno, titulo=titulo, tema=rodaje.get("tema"),
                              motivo=rodaje.get("motivo"), forma=rodaje.get("forma"), apertura=apertura(rodaje)
                              or frase.get("objetivo_visual"), primera_frase=frase.get("texto"),
                              archivo=str(p.relative_to(carpeta.parent))))
    return filas


def validar(guion):
    titulo = texto(guion, "titulo", "el guion")
    rodaje = guion.get("rodaje")
    if not isinstance(rodaje, dict):
        raise ValueError("Falta rodaje en el guion. Consulta herramientas/GUION.md.")
    for campo in ("turno", "tema", "motivo", "forma", "direccion", "pregunta", "respuesta", "pie_de_foto", "cierre"):
        texto(rodaje, campo, "rodaje")
    fuentes = rodaje.get("fuentes_comerciales")
    if not isinstance(fuentes, list):
        raise ValueError("Indica fuentes_comerciales, o [] si el guion carece de afirmaciones comerciales.")
    for fuente in fuentes:
        for campo in ("dato", "fuente", "vigencia"):
            texto(fuente, campo, "fuentes_comerciales")
    frases = guion.get("frases")
    if not isinstance(frases, list) or not frases:
        raise ValueError("Falta la locución literal en frases.")
    ids = []
    for frase in frases:
        ids.append(texto(frase, "id", "frases"))
        texto(frase, "texto", ids[-1])
        texto(frase, "objetivo_visual", ids[-1])
    if len(set(ids)) != len(ids) or texto(rodaje, "cta_frase", "rodaje") != ids[-1]:
        raise ValueError("Usa ID de frase únicos y señala la última frase hablada como único CTA.")
    escenas = rodaje.get("escenas")
    if not isinstance(escenas, list) or not escenas:
        raise ValueError("Faltan las escenas de rodaje.")
    usadas = []
    for n, escena in enumerate(escenas, 1):
        donde = f"escena {n}"
        texto(escena, "sonido", donde)
        for bloque, campos in BLOQUES.items():
            for campo in campos:
                texto(escena.get(bloque), campo, f"{donde}, {bloque}")
        segundos = escena.get("segundos")
        if type(segundos) not in (int, float) or not math.isfinite(segundos) or segundos <= 0:
            raise ValueError(f"Indica segundos aproximados positivos en {donde}.")
        if "texto_grafico" not in escena:
            raise ValueError(f"Indica el texto_grafico o null en {donde}.")
        if escena["texto_grafico"] is not None:
            texto(escena, "texto_grafico", donde)
        voces = escena.get("frases")
        if not isinstance(voces, list) or not all(isinstance(v, str) for v in voces):
            raise ValueError(f"Indica los ID de locución o [] para sonido solo en {donde}.")
        if voces and escena.get("intencion") not in INTENCIONES:
            raise ValueError(f"Elige una intención de voz para {donde}: {', '.join(INTENCIONES)}.")
        usadas.extend(voces)
    if usadas != ids:
        raise ValueError("Las escenas deben cubrir exactamente las frases habladas, en orden.")
    return {"titulo": titulo, "turno": rodaje["turno"], "escenas": len(escenas),
            "duracion_estimada": round(sum(e["segundos"] for e in escenas), 3)}


def validar_turno(carpeta, guion):
    resumen = validar(guion)
    rodaje = guion["rodaje"]
    propuesto = {"titulo": resumen["titulo"], "tema": rodaje["tema"], "motivo": rodaje["motivo"],
                 "forma": rodaje["forma"], "apertura": apertura(rodaje)}
    for otro in historial(carpeta):
        if otro["fecha"] != carpeta.name or not otro["turno"] or otro["turno"] == rodaje["turno"]:
            continue
        for campo, valor in propuesto.items():
            existente = otro.get(campo)
            if existente and " ".join(existente.casefold().split()) == " ".join(valor.casefold().split()):
                raise ValueError(f"El turno {otro['turno']} ya usa el mismo campo {campo}. Revisa {otro['archivo']}.")
    return resumen


def hoja(guion):
    resumen = validar(guion)
    rodaje = guion["rodaje"]
    frases = {f["id"]: f["texto"] for f in guion["frases"]}
    lineas = [f"# {resumen['titulo']}", "", f"Turno {rodaje['turno']} · {resumen['duracion_estimada']:g} s estimados",
              "", rodaje["direccion"], "", f"**Motivo para verlo** · {rodaje['motivo']}",
              "", f"**Pregunta que abre la historia** · {rodaje['pregunta']}",
              "", f"**Respuesta que debe verse** · {rodaje['respuesta']}",
              "", "Rodar en vertical 9:16, con el horizonte derecho. Grabar un segundo antes y después de cada gesto.",
              "Subtítulos grandes y legibles, sincronizados con la voz definitiva."]
    inicio = 0
    for n, escena in enumerate(rodaje["escenas"], 1):
        fin = inicio + escena["segundos"]
        voces = escena["frases"]
        locucion = f"({escena['intencion']}) " + " ".join(frases[v] for v in voces) if voces else "Solo sonido de escena."
        toma, camara, edicion = (escena[k] for k in ("toma", "camara", "edicion"))
        lineas.extend(["", f"## Escena {n} · {inicio:g}–{fin:g} s", "", f"**Locución** · {locucion}",
                       "", f"**Toma** · {toma['quien']} · {toma['accion']} · {toma['fin']}",
                       "", f"**Cámara** · {camara['posicion']} · {camara['plano']} · Foco en {camara['foco']}.",
                       "", f"**Entrada** · {edicion['entrada']}", "", f"**Corte** · {edicion['corte']}",
                       "", f"**Continuidad** · {edicion['enlace']}", "", f"**Sonido** · {escena['sonido']}",
                       "", f"**Texto gráfico** · {escena['texto_grafico'] or 'Plano limpio.'}"])
        inicio = fin
    lineas.extend(["", "## Cierre", "", rodaje["cierre"], "", "## Texto de publicación", "", rodaje["pie_de_foto"]])
    if rodaje["fuentes_comerciales"]:
        lineas.extend(["", "## Respaldo de marca", ""])
        for f in rodaje["fuentes_comerciales"]:
            lineas.append(f"- {f['dato']} · {f['fuente']} · {f['vigencia']}")
    return "\n".join(lineas) + "\n"
