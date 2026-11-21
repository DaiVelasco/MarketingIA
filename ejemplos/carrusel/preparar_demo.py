"""Genera una orden y arte de ensayo con ilustraciones sintéticas dentro de una jornada vacía."""
from argparse import ArgumentParser
from html import escape
import json
from pathlib import Path


PAGINAS = (
    ("¿Se lee a primera vista?", "Una prueba de contraste en cuatro láminas.", "#153730", "#c8ffc0"),
    ("Fondo claro", "Las letras oscuras resaltan sobre una superficie clara.", "#eef3ea", "#174a3a"),
    ("Fondo oscuro", "Cambia el color del texto al cambiar el fondo.", "#162a25", "#e5ffe0"),
    ("Mira el conjunto", "Guárdalo para revisar tu próximo diseño.", "#22433b", "#f2f7c5"),
)


def preparar(jornada):
    guion, carrusel = jornada / "guion", jornada / "carrusel"
    arte = carrusel / "arte"
    if not (jornada / "brief.md").is_file() or not guion.is_dir():
        raise ValueError("Primero crea la jornada de ensayo con campana.py iniciar.")
    if (guion / "carrusel-01.json").exists() or (carrusel / "pie-de-foto.txt").exists() or any(arte.iterdir()):
        raise ValueError("La jornada ya contiene un carrusel. Usa una jornada de ensayo vacía.")
    recursos = arte / "recursos"
    recursos.mkdir()
    laminas = []
    for pos, (titulo, cuerpo, fondo, tinta) in enumerate(PAGINAS, 1):
        img = recursos / f"muestra-{pos}.svg"
        img.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="850" height="450" viewBox="0 0 850 450">'
            f'<rect width="850" height="450" rx="24" fill="{tinta}"/>'
            f'<circle cx="{170*pos}" cy="225" r="110" fill="{fondo}"/></svg>', encoding="utf-8")
        laminas.append({
            "numero": pos, "titulo": titulo, "cuerpo": cuerpo, "imagen": img.relative_to(jornada).as_posix(),
            "recorte": "Ilustración completa, centrada, 850 × 450 px.",
            "capas": [f"Fondo {fondo}", "Ilustración", f"Titular y cuerpo en {tinta}"],
            "tipografia": "Arial, 77 px en el titular y 46 px en el texto.",
            "posicion": "Ilustración en x=115 y=225. Texto en x=115 y=785.",
            "control": "La figura y el texto se distinguen del fondo.",
            "alt": f"Figura circular en una muestra de contraste. {titulo} {cuerpo}",
        })
    for indice, pos in enumerate([1, 2, 3, 4, 1, 4], 1):
        titulo, cuerpo, fondo, tinta = PAGINAS[pos - 1]
        alto = 1350 if indice <= 4 else 1920
        page = f"""<!doctype html><html lang="es"><meta charset="utf-8"><style>
            * {{box-sizing:border-box}} body,h1,p {{margin:0}}
            main {{position:relative;width:1080px;height:{alto}px;background:{fondo};color:{tinta};font-family:Arial,sans-serif}}
            img {{position:absolute;left:115px;top:{225 if indice<=4 else 390}px;width:850px;height:450px}}
            article {{position:absolute;left:115px;top:{785 if indice<=4 else 975}px;width:850px}}
            h1 {{font-size:77px}} p {{font-size:46px;margin-top:30px}} </style>
            <main><img alt="" src="recursos/muestra-{pos}.svg"><article>
            <h1>{escape(titulo)}</h1><p>{escape(cuerpo)}</p></article></main></html>"""
        (arte / f"{indice:02d}.html").write_text(page, encoding="utf-8")
    orden = {"cuenta": jornada.parent.name, "objetivo": "Reconocer el contraste",
             "cta": PAGINAS[-1][1], "formato": [1080, 1350], "laminas": laminas}
    (guion / "carrusel-01.json").write_text(json.dumps(orden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (carrusel / "pie-de-foto.txt").write_text("Prueba el texto sobre ambos fondos. "
                                                + PAGINAS[-1][1] + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("jornada", type=Path)
    try:
        preparar(parser.parse_args().jornada.resolve())
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
