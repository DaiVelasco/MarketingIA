"""Converzzo en MarketingIA: catálogo, instalación local, modelos y render por plugin."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "integraciones/converzzo"
MARKET = DIST / "marketplace"
LOCAL = ROOT / ".local/converzzo"
PYTHON = LOCAL / "python" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
LOCK = json.loads((DIST / "versiones.json").read_text(encoding="utf-8"))
PLUGINS = tuple(LOCK["plugins"])
CACHE = LOCAL / "motores/efectos-converzzo/motor/models/hf"


def run(args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def command(name):
    path = shutil.which(name)
    if not path:
        raise ValueError(f"Falta {name} en PATH.")
    return path


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def skills(plugin):
    return sorted(p.parent.name for p in (MARKET / "plugins" / plugin / "skills").glob("*/SKILL.md"))


def model_path(model):
    return CACHE / ("models--" + model["repo"].replace("/", "--")) / "snapshots" / model["commit"]


def runtime(plugin):
    return LOCAL / "motores" / plugin


def engine_sources(plugin):
    pin = LOCK["plugins"][plugin]
    dest = runtime(plugin)
    origin = dest / "ORIGEN.txt"
    patch = DIST / "parches" / (plugin + ".patch")
    stamp = dest / "ADAPTACION.txt"
    signature = f"{pin['commit']} {digest(patch)} guia-codex-1"
    if origin.exists() and origin.read_text(encoding="utf-8").splitlines() != [pin["repo"], pin["commit"]]:
        raise ValueError(f"Origen distinto al fijado en {dest}. Conserva esa instalación en otra ruta antes de preparar.")
    if dest.exists() and not origin.exists() and any(dest.iterdir()):
        raise ValueError(f"Motor existente sin ORIGEN.txt en {dest}.")
    if stamp.is_file() and stamp.read_text().strip() == signature and (dest / "motor/render.mjs").is_file():
        return
    # Aplicar siempre el parche en un checkout limpio del commit verificado.
    with tempfile.TemporaryDirectory(prefix="fuente-", dir=LOCAL) as tmp:
        repo = Path(tmp)
        git = [command("git"), "-c", "core.autocrlf=false", "-C", repo]
        run([*git, "init", "-q"])
        run([*git, "fetch", "-q", "--depth=1", pin["repo"], pin["commit"]])
        run([*git, "checkout", "-q", "--detach", "FETCH_HEAD"])
        head = subprocess.check_output([*map(str, git), "rev-parse", "HEAD"], text=True).strip()
        if head != pin["commit"]:
            raise ValueError(f"El commit descargado de {plugin} no coincide.")
        run([*git, "apply", "--whitespace=nowarn", patch])
        src = repo / "plugins" / plugin
        dest.mkdir(parents=True, exist_ok=True)
        origin.write_text(pin["repo"] + "\n" + head + "\n", encoding="utf-8")
        shutil.copytree(src / "motor", dest / "motor", dirs_exist_ok=True)
        for filename in ("VERSION", "NOTICE.md", "LICENSE", "catalogo-fuentes.png"):
            if (src / filename).is_file():
                shutil.copy2(src / filename, dest / filename)
        guide = (src / "GUIA.md").read_text(encoding="utf-8")
        guide = guide.replace("~/.claude/" + plugin, dest.as_posix())
        guide = guide.replace("Guía para Claude", "Guía para Codex").replace(" (lo deja listo `preparar.sh` del plugin)", "")
        # Rutas relativas al motor original que cambian al compartir un entorno Python.
        guide = "\n".join(
            f"- `PY` = `{PYTHON.as_posix()}`." if line.startswith("- `PY` =") else line
            for line in guide.split("\n")
        )
        (dest / "GUIA.md").write_text(guide, encoding="utf-8")
        stamp.write_text(signature + "\n", encoding="ascii")


def prepare():
    uv = command("uv")
    npm = command("npm.cmd" if os.name == "nt" else "npm")
    LOCAL.mkdir(parents=True, exist_ok=True)
    if not PYTHON.exists():
        run([uv, "venv", "--python", sys.executable, LOCAL / "python"])
    for plugin in PLUGINS:
        engine_sources(plugin)
        run([npm, "install", "--no-audit", "--no-fund"], cwd=runtime(plugin) / "motor")
    requirements = []
    for plugin in PLUGINS:
        requirements.extend(["-r", runtime(plugin) / "motor/requirements.txt"])
    run([uv, "pip", "install", "--python", PYTHON, *requirements])


def activate():
    # Keep the same catalogue path when updating earlier MarketingIA workstations.
    local_market = LOCAL / "marketplace"
    shutil.copytree(MARKET, local_market, dirs_exist_ok=True)
    codex = command("codex")
    run([codex, "plugin", "marketplace", "add", local_market])
    for plugin in PLUGINS:
        run([codex, "plugin", "add", plugin + "@converzzo-marketingia"])


def download_models():
    from huggingface_hub import snapshot_download
    for model in LOCK["modelos"]:
        path = model_path(model)
        options = dict(repo_id=model["repo"], revision=model["commit"], cache_dir=str(CACHE),
                       allow_patterns=["*.json", "model.safetensors", "LICENSE*"])
        files = ["config.json", "preprocessor_config.json", "model.safetensors"]
        if model["repo"] == "facebook/sam2.1-hiera-small":
            files.extend(["processor_config.json", "video_preprocessor_config.json"])
        if not all((path / f).is_file() for f in files):
            snapshot_download(**options)
        if digest(path / "model.safetensors") != model["sha256"]:
            snapshot_download(**options, force_download=True)
            if digest(path / "model.safetensors") != model["sha256"]:
                raise ValueError("El SHA-256 del modelo no coincide: " + model["repo"])
        ref = path.parent.parent / "refs/main"
        ref.parent.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=ref.parent, delete=False) as fp:
            fp.write(model["commit"].encode("ascii"))
        os.replace(fp.name, ref)
        print(model["repo"], model["commit"], "verificado")


def install_models():
    if not PYTHON.is_file():
        raise ValueError("Primero ejecuta preparar.")
    run([command("uv"), "pip", "install", "--python", PYTHON, "--torch-backend", "cpu",
         "torch==2.15.0", "torchvision==0.29.2", "transformers==4.57.6"])
    run([PYTHON, Path(__file__).resolve(), "_descargar"])


def render(args):
    motor = runtime(args.plugin) / "motor"
    if not PYTHON.is_file() or not (motor / "node_modules/@remotion/cli/remotion-cli.js").is_file():
        raise ValueError("Falta el motor local. Ejecuta preparar.")
    video, plan, output = (p.resolve() for p in (args.video, args.plan, args.salida))
    if not video.is_file() or not plan.is_file():
        raise ValueError("Falta el video o el plan indicado.")
    if video == output or plan == output or (output.exists() and not args.still):
        raise ValueError("Usa una ruta de salida nueva.")
    env = dict(os.environ, PYTHONUTF8="1")
    if args.evidencia:
        if args.plugin != "efectos-converzzo":
            raise ValueError("--evidencia corresponde al plan ejecutado del motor de efectos.")
        proof = args.evidencia.resolve()
        if proof in (video, plan, output) or proof.exists():
            raise ValueError("Usa una ruta de evidencia nueva, distinta de la entrada y la salida.")
        env["EFECTOS_PLAN_FINAL"] = str(proof)
    cmd = [command("node"), motor / "render.mjs", video, plan, output]
    if args.still:
        cmd.extend(["--still", args.still])
    run(cmd, cwd=motor, env=env)


def state():
    for plugin in PLUGINS:
        motor = runtime(plugin) / "motor"
        installed = (motor / "render.mjs").is_file() and (motor / "node_modules/@remotion/cli/remotion-cli.js").is_file()
        print(f"{plugin}: {len(skills(plugin))} skills; motor " + ("presente" if installed else "pendiente"))
    print("Entorno Python:", "presente" if PYTHON.is_file() else "pendiente")
    for model in LOCK["modelos"]:
        weight = model_path(model) / "model.safetensors"
        ok = weight.is_file() and digest(weight) == model["sha256"]
        print(model["repo"], "pesos verificados" if ok else "pesos pendientes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="accion", required=True)
    cat = commands.add_parser("catalogo")
    cat.add_argument("plugin", choices=PLUGINS, nargs="?")
    for name in ("estado", "preparar", "activar", "modelos", "_descargar"):
        commands.add_parser(name)
    rend = commands.add_parser("render")
    rend.add_argument("plugin", choices=PLUGINS)
    for name in ("video", "plan", "salida"):
        rend.add_argument(name, type=Path)
    rend.add_argument("--evidencia", type=Path)
    rend.add_argument("--still", help="Segundos separados por comas para fotos de control")
    args = parser.parse_args()
    if args.accion == "catalogo":
        for plugin in ([args.plugin] if args.plugin else PLUGINS):
            print(plugin + "\n  " + ", ".join(skills(plugin)))
    elif args.accion == "render":
        render(args)
    else:
        {"estado": state, "preparar": prepare, "activar": activate,
         "modelos": install_models, "_descargar": download_models}[args.accion]()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from exc
