"""Ejecuta las herramientas de sonido con el entorno y el banco de MarketingIA."""
import argparse
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local" / "sonido"
SKILLS = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("herramienta", choices=("earshot", "real-sfx", "real-sound", "diseno-sonido", "openverse", "commons"))
    parser.add_argument("argumentos", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    scripts = LOCAL / "venv" / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    python = scripts / ("python" + suffix)
    if not python.is_file():
        parser.exit(1, "Instala el entorno siguiendo integraciones/sonido/README.md.\n")
    env = os.environ.copy()
    env.update(PATH=os.pathsep.join((str(scripts), str(ROOT / ".local"), env.get("PATH", ""))),
               PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.setdefault("SONIDOS_DIR", str(LOCAL / "banco"))
    extra = args.argumentos
    if args.herramienta == "earshot":
        command = [scripts / ("earshot" + suffix)]
    elif args.herramienta == "commons":
        command = [python, ROOT / "herramientas" / "commons_audio.py"]
    elif args.herramienta in ("openverse", "diseno-sonido"):
        script = "openverse.py" if args.herramienta == "openverse" else "diseno.py"
        command = [python, ROOT / "skills" / "diseno-sonido" / "scripts" / script]
    else:
        folder = SKILLS / args.herramienta / "scripts"
        if not folder.is_dir():
            parser.exit(1, f"Falta instalar {args.herramienta} en {SKILLS}.\n")
        available = {p.stem: p for p in folder.glob("*.py") if not p.name.startswith("_")}
        if not extra or extra[0] not in available:
            parser.exit(0 if not extra or extra[0] in ("-h", "--help") else 2,
                        "Scripts disponibles: " + ", ".join(sorted(available)) + "\n")
        if args.herramienta == "real-sfx" and "REAL_SFX_CONFIG" not in env:
            bank = Path(env["SONIDOS_DIR"]).resolve()
            libraries = [{"name": name, "path": str(bank / name), "tier": "main"}
                         for name in ("grabaciones", "openverse")]
            for lib in libraries:
                Path(lib["path"]).mkdir(parents=True, exist_ok=True)
            config = bank / "real-sfx.json"
            if not config.exists():
                data = {"libraries": libraries, "index_path": str(bank / "indice-real-sfx.json")}
                config.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            env["REAL_SFX_CONFIG"] = str(config)
        command = [python, *(["-I"] if args.herramienta == "real-sound" else []), available[extra[0]]]
        extra = extra[1:]
    return subprocess.run([*command, *extra], env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
