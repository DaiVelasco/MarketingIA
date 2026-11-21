"""Valida las instrucciones que recibe Diseño antes de montar un carrusel en Canva."""
from .edicion_reel import cargar, local, sha256, texto


def orden_carrusel(folder, version):
    if version < 1:
        raise ValueError("Indica una revisión positiva del carrusel.")
    path = folder / "guion" / f"carrusel-{version:02}.json"
    plan = cargar(path)
    if any(not texto(plan.get(key)) for key in ("cuenta", "objetivo", "cta")):
        raise ValueError("La orden necesita cuenta, objetivo y CTA.")
    if plan.get("formato") != [1080, 1350]:
        raise ValueError("El formato del carrusel debe ser de 1080 × 1350 px.")
    pages = plan.get("laminas")
    if not isinstance(pages, list) or len(pages) != 4:
        raise ValueError("Entrega las cuatro láminas en orden de lectura.")
    images = {}
    for number, page in enumerate(pages, 1):
        if not isinstance(page, dict) or type(page.get("numero")) != int or page["numero"] != number:
            raise ValueError(f"La posición {number} debe contener la lámina {number}.")
        for key in ("titulo", "imagen", "recorte", "tipografia", "posicion", "control", "alt"):
            if not texto(page.get(key)):
                raise ValueError(f"Falta {key} en la lámina {number}.")
        if not isinstance(page.get("cuerpo"), str):
            raise ValueError(f"Indica el cuerpo literal de la lámina {number}, incluso si va vacío.")
        layers = page.get("capas")
        if not isinstance(layers, list) or len(layers) < 2 or not all(map(texto, layers)):
            raise ValueError(f"Ordena las capas de fondo a frente en la lámina {number}.")
        image = local(folder, page["imagen"])
        images[image.relative_to(folder.resolve()).as_posix()] = sha256(image)
    return {"orden": path, "orden_sha256": sha256(path), "imagenes": images}
