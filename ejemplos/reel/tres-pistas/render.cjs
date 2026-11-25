const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {createRequire} = require("node:module");

async function main(args) {
  const still = args[0] === "--still";
  if ((still && (args.length !== 3 || !/^\d+$/.test(args[1]) || Number(args[1]) >= 336)) ||
      (!still && args.length !== 1)) {
    throw new Error("Uso: node render.cjs salida.mov o node render.cjs --still CUADRO salida.png (0–335)");
  }
  const output = path.resolve(args.at(-1));
  if (fs.existsSync(output)) throw new Error("La salida ya existe: " + output);
  const motors = path.resolve(process.env.CONVERZZO_MOTORES || path.join(__dirname, "../../../.local/converzzo/motores"));
  const engine = path.join(motors, "efectos-converzzo/motor");
  const load = createRequire(path.join(engine, "package.json"));
  const {bundle} = load("@remotion/bundler");
  const {selectComposition, renderMedia, renderStill} = load("@remotion/renderer");
  const tmpRoot = path.resolve(os.tmpdir());
  const temp = fs.mkdtempSync(path.join(tmpRoot, "remotion-tres-pistas-"));
  try {
    const assets = path.join(temp, "public");
    fs.mkdirSync(assets);
    for (const font of ["ArchivoBlack.ttf", "SpaceGrotesk.ttf"]) {
      fs.copyFileSync(path.join(motors, "tipografia-converzzo/motor/public/fonts", font), path.join(assets, font));
    }
    const serveUrl = await bundle({
      entryPoint: path.join(__dirname, "Pistas.jsx"), publicDir: assets,
      outDir: path.join(temp, "bundle"), enableCaching: false,
      webpackOverride: cfg => ({...cfg, resolve: {...cfg.resolve, modules: [path.join(engine,"node_modules"), ...(cfg.resolve.modules || [])]}}),
    });
    const browserExecutable = process.env.CONVERZZO_CHROME || [
      "C:/Program Files/Google/Chrome/Application/chrome.exe",
      "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/usr/bin/google-chrome", "/usr/bin/chromium",
    ].find(file => fs.existsSync(file));
    const common = {serveUrl, browserExecutable, logLevel: "error"};
    const composition = await selectComposition({...common, id: "TresPistas"});
    if (still) {
      await renderStill({...common, composition, frame: Number(args[1]), imageFormat: "png", output});
    } else {
      await renderMedia({...common, composition, codec: "prores", proResProfile: "4444", imageFormat: "png",
        pixelFormat: "yuva444p10le", muted: true, concurrency: 3, outputLocation: output, overwrite: false});
    }
    console.log(output);
  } finally {
    if (path.dirname(temp) === tmpRoot && path.basename(temp).startsWith("remotion-tres-pistas-")) {
      fs.rmSync(temp, {recursive: true, force: true});
    }
  }
}

main(process.argv.slice(2)).catch(error => {console.error(error.message); process.exitCode = 1;});
