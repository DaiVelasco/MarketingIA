const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {createRequire} = require('node:module');

async function main([id, ...args]) {
  const still = args[0] === '--still';
  if (!['RadarCabina', 'Copiloto'].includes(id) ||
      (still ? args.length !== 3 || !/^\d+$/.test(args[1]) : args.length !== 1)) {
    throw new Error('Uso: render.cjs RadarCabina|Copiloto salida.mov o render.cjs RadarCabina|Copiloto --still CUADRO salida.png');
  }
  const output = path.resolve(args.at(-1));
  if (fs.existsSync(output)) throw new Error('El archivo de salida ya existe: ' + output);

  const motors = path.resolve(process.env.CONVERZZO_MOTORES || path.join(__dirname, '../../../.local/converzzo/motores'));
  const engine = path.join(motors, 'efectos-converzzo/motor');
  const load = createRequire(path.join(engine, 'package.json'));
  const {bundle} = load('@remotion/bundler');
  const {selectComposition, renderMedia, renderStill} = load('@remotion/renderer');
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'konduce-pronostico-'));
  try {
    const assets = path.join(temp, 'public');
    fs.mkdirSync(assets);
    for (const font of ['ArchivoBlack.ttf', 'SpaceGrotesk.ttf']) {
      fs.copyFileSync(path.join(motors, 'tipografia-converzzo/motor/public/fonts', font), path.join(assets, font));
    }
    const serveUrl = await bundle({
      entryPoint: path.join(__dirname, 'Parte.jsx'), publicDir: assets,
      outDir: path.join(temp, 'bundle'), enableCaching: false,
      webpackOverride: config => ({...config, resolve: {...config.resolve,
        modules: [path.join(engine, 'node_modules'), ...(config.resolve.modules || [])]}}),
    });
    const browserExecutable = process.env.CONVERZZO_CHROME || [
      'C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/usr/bin/google-chrome', '/usr/bin/chromium',
    ].find(file => fs.existsSync(file));
    const options = {serveUrl, browserExecutable, logLevel: 'error'};
    const composition = await selectComposition({...options, id});
    if (still) {
      const frame = Number(args[1]);
      if (frame >= composition.durationInFrames) throw new Error('El fotograma queda fuera de la composición.');
      await renderStill({...options, composition, frame, imageFormat: 'png', output});
    } else {
      await renderMedia({...options, composition, codec: 'prores', proResProfile: '4444', pixelFormat: 'yuva444p10le',
        imageFormat: 'png', muted: true, concurrency: 3, outputLocation: output, overwrite: false});
    }
  } finally {
    fs.rmSync(temp, {recursive: true, force: true});
  }
}

main(process.argv.slice(2)).catch(error => {console.error(error.message); process.exitCode = 1;});
