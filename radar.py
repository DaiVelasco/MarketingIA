"""Instantáneas comparables de reels de la marca y cuentas de referencia."""
import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3
from statistics import median
import sys

from campana import ROOT, cfg
from instagram import Meta, numeric


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.execute("""CREATE TABLE IF NOT EXISTS muestras (
        cuenta TEXT NOT NULL, medio TEXT NOT NULL, publicado TEXT NOT NULL,
        observado TEXT NOT NULL, edad REAL NOT NULL, vistas INTEGER NOT NULL,
        enlace TEXT NOT NULL, PRIMARY KEY(cuenta, medio, observado))""")
    return db


def collect(db):
    settings = cfg()
    api = Meta()
    api.identity(settings)
    now = dt.datetime.now(dt.timezone.utc)
    warnings = []
    sampled = 0

    def save(account, item, own):
        nonlocal sampled
        if item.get("media_product_type") != "REELS":
            return
        published = dt.datetime.fromisoformat(item["timestamp"]).astimezone(dt.timezone.utc)
        hours = (now - published).total_seconds() / 3600
        if not 60 <= hours <= 84:
            return
        value = item.get("view_count")
        if own:
            insight = api.api(numeric(item["id"]) + "/insights", {"metric": "views"})
            values = next((x.get("values", []) for x in insight["data"] if x.get("name") == "views"), [])
            value = values[-1].get("value") if values else None
        if not isinstance(value, int) or value < 0:
            warnings.append(f"{account}/{item['id']}: vistas no disponibles")
            return
        with db:
            db.execute("INSERT OR IGNORE INTO muestras VALUES (?,?,?,?,?,?,?)",
                       (account, item["id"], published.isoformat(), now.isoformat(), hours, value, item.get("permalink", "")))
        sampled += 1

    accounts = [settings["cuenta"]] + list(dict.fromkeys(settings["referencias"]))
    for index, name in enumerate(accounts):
        try:
            if not index:
                rows = api.pages(api.account + "/media", "id,timestamp,media_product_type,permalink")
            else:
                import re
                if not re.fullmatch(r"[A-Za-z0-9_.]{1,30}", name):
                    raise ValueError("Utiliza el nombre sin @.")
                fields = f"business_discovery.username({name}){{media.limit(50){{id,timestamp,media_product_type,permalink,view_count}}}}"
                data = api.api(api.account, {"fields": fields}, discovery=True)
                rows = data["business_discovery"]["media"]["data"]
            for item in rows:
                try:
                    save(name, item, not index)
                except (RuntimeError, OSError, ValueError, KeyError) as exc:
                    warnings.append(f"{name}/{item.get('id')}: {exc}")
        except (RuntimeError, OSError, ValueError, KeyError) as exc:
            warnings.append(f"{name}: {exc}")
    return {"muestras_recogidas": sampled, "avisos": warnings, "ventana_horas": [60, 84]}


def rank(db):
    # Closest snapshot to 72h, one per reel; previous distinct reels form the baseline.
    rows = db.execute("""SELECT cuenta, medio, publicado, edad, vistas, enlace FROM muestras
                      WHERE edad BETWEEN 60 AND 84 ORDER BY cuenta, publicado, medio, ABS(edad-72), observado""")
    selected = {}
    for account, mid, published, hours, views, url in rows:
        selected.setdefault(account, {}).setdefault(mid, (published, hours, views, url))
    ranked, missing = [], []
    for account, entries in selected.items():
        history = []
        for mid, (published, hours, views, url) in entries.items():
            comparable = [count for earlier, count in history if earlier < published][-12:]
            baseline = median(comparable) if len(comparable) >= 5 else 0
            if baseline:
                ranked.append({"cuenta": account, "medio": mid, "publicado": published, "enlace": url,
                               "vistas": views, "edad_horas": round(hours, 1), "n_referencia": len(comparable),
                               "mediana": baseline, "multiplo": round(views / baseline, 2)})
            else:
                missing.append({"cuenta": account, "medio": mid, "n_referencia": len(comparable)})
            history.append((published, views))
    return {"comparables": sorted(ranked, key=lambda x: x["multiplo"], reverse=True), "sin_base": missing}


def demo():
    db = connect(":memory:")
    for i, views in enumerate([1000, 800, 1100, 900, 1200, 3200], start=1):
        published = dt.datetime(2026, 1, i, tzinfo=dt.timezone.utc)
        seen = published + dt.timedelta(hours=72)
        db.execute("INSERT INTO muestras VALUES (?,?,?,?,?,?,?)", ("ejemplo_ficticio", str(i), published.isoformat(), seen.isoformat(), 72, views, ""))
    return {"tipo": "simulacion_sin_red", **rank(db)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accion", choices=["capturar", "clasificar", "demo"])
    args = parser.parse_args()
    try:
        if args.accion == "demo":
            result = demo()
        else:
            state = ROOT / "estado"
            state.mkdir(exist_ok=True)
            db = connect(state / "radar.sqlite")
            result = collect(db) if args.accion == "capturar" else rank(db)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (RuntimeError, ValueError, KeyError, OSError, sqlite3.Error) as error:
        sys.exit(str(error))
