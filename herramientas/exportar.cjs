// Ejecutar con Node.js 20 o posterior desde cualquier directorio.
const fs = require('node:fs/promises');
const { existsSync } = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright-core');
const JSZip = require('jszip');

const piezas = Array.from({length: 6}, (_, i) => ({
  html: String(i + 1).padStart(2, '0') + '.html',
  jpg: (i < 4 ? 'carrusel/' : 'historias/') + String(i < 4 ? i + 1 : i - 3).padStart(2, '0') + '.jpg',
  alto: i < 4 ? 1350 : 1920,
}));
const vistas = ['vista-carrusel.jpg', 'vista-historias.jpg'];

function opciones(args) {
  if (!args.length || args[0].startsWith('--')) throw Error('Uso: node herramientas/exportar.cjs CARPETA [--verificar] [--revision N]');
  let revision = 1;
  let verificar = false;
  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--verificar') verificar = true;
    else if (args[i] === '--revision' && /^[1-9]\d*$/.test(args[i+1] || '')) revision = Number(args[++i]);
    else throw Error('Opción desconocida o revisión inválida: ' + args[i]);
  }
  const base = path.resolve(args[0]);
  return { base, destino: path.join(base, revision === 1 ? 'entrega' : 'entrega-v' + revision), verificar };
}

function buscarNavegador() {
  const personalizado = process.env.MARKETING_BROWSER;
  if (personalizado) {
    if (!existsSync(personalizado)) throw Error('MARKETING_BROWSER apunta a un ejecutable inexistente.');
    return personalizado;
  }
  const candidatos = [chromium.executablePath()];
  if (process.platform === 'win32') {
    const directorios = [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA].filter(Boolean);
    for (const dir of directorios) {
      candidatos.push(path.join(dir, 'Microsoft/Edge/Application/msedge.exe'), path.join(dir, 'Google/Chrome/Application/chrome.exe'));
    }
  } else if (process.platform === 'darwin') {
    for (const dir of ['/Applications', path.join(os.homedir(), 'Applications')]) {
      candidatos.push(path.join(dir,'Google Chrome.app/Contents/MacOS/Google Chrome'), path.join(dir,'Microsoft Edge.app/Contents/MacOS/Microsoft Edge'), path.join(dir,'Chromium.app/Contents/MacOS/Chromium'));
    }
  } else {
    candidatos.push('/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/opt/google/chrome/chrome', '/usr/bin/microsoft-edge', '/snap/bin/chromium');
  }
  const encontrado = candidatos.find(c => existsSync(c));
  if (!encontrado) throw Error('Falta un navegador Chromium. Consulta herramientas/DISENO.md para instalarlo o indicar su ruta.');
  return encontrado;
}

function dimensionesJPEG(buffer) {
  if (buffer.readUInt16BE(0) !== 0xffd8 || buffer.readUInt16BE(buffer.length-2) !== 0xffd9) throw Error('JPEG incompleto');
  let pos = 2;
  while (pos + 9 < buffer.length && buffer[pos] === 0xff) {
    const marca = buffer[pos + 1];
    if ([0xc0, 0xc1, 0xc2].includes(marca)) return [buffer.readUInt16BE(pos+7), buffer.readUInt16BE(pos+5)];
    const longitud = buffer.readUInt16BE(pos+2);
    if (longitud < 2 || marca === 0xda) break;
    pos += longitud + 2;
  }
  throw Error('No se pudieron leer las dimensiones JPEG.');
}

async function verificarEntrega(dir) {
  const zip = await JSZip.loadAsync(await fs.readFile(path.join(dir,'instagram.zip')), {checkCRC32: true});
  const nombres = [...piezas.map(p => p.jpg), 'pie-de-foto.txt'];
  if (Object.values(zip.files).filter(f=>!f.dir).length !== nombres.length) throw Error('El ZIP debe contener seis JPG y un pie de foto.');
  for (const nombre of nombres) {
    const original = await fs.readFile(path.join(dir,'publicar',nombre));
    const entrada = zip.file(nombre);
    if (!entrada || !(await entrada.async('nodebuffer')).equals(original)) throw Error('El ZIP y el original difieren: ' + nombre);
    const pieza = piezas.find(p=>p.jpg===nombre);
    if (pieza && dimensionesJPEG(original).join('x') !== '1080x' + pieza.alto) throw Error('Dimensiones incorrectas: ' + nombre);
    if (!pieza && !original.toString('utf8').trim()) throw Error('El pie de foto está vacío.');
  }
  for (const vista of vistas) dimensionesJPEG(await fs.readFile(path.join(dir, vista)));
}

async function exportarPieza(browser, base, pieza, publicar) {
  const page = await browser.newPage({viewport:{width:1080,height:pieza.alto},deviceScaleFactor:1});
  try {
    const errores = [];
    page.on('pageerror', e=>errores.push(e.message));
    page.on('requestfailed', r=>errores.push(r.url().split('?')[0]));
    await page.route(/^https?:\/\//i, route=>route.abort());
    await page.goto(pathToFileURL(path.join(base,'arte', pieza.html)).href,{waitUntil:'load',timeout:20000});
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all(Array.from(document.images, img => img.decode()));
    });
    const principal = page.locator('main');
    if (await principal.count() !== 1) throw Error('La pieza debe definir un único elemento main.');
    const rect = await principal.boundingBox();
    if (!rect || rect.width !== 1080 || rect.height !== pieza.alto) throw Error('El lienzo main debe medir 1080 × ' + pieza.alto + ' px.');
    const contenido = await principal.evaluate(el => Boolean(el.innerText.trim() || el.querySelector('img,svg,canvas,picture') || getComputedStyle(el).backgroundImage !== 'none'));
    if (!contenido || errores.length) throw Error('Arte vacío o recurso sin cargar. ' + errores.join(', '));
    await principal.screenshot({path:path.join(publicar,pieza.jpg),type:'jpeg',quality:95,animations:'disabled'});
  } catch (err) {
    throw Error(pieza.html + ': ' + err.message);
  } finally { await page.close(); }
}

async function crearVista(browser, dir, grupo, archivo) {
  const ancho = grupo.length === 4 ? 330 : 360;
  const fotos = await Promise.all(grupo.map(async p=>{
    const datos = await fs.readFile(path.join(dir,'publicar',p.jpg));
    return '<img width="'+ancho+'" src="data:image/jpeg;base64,'+datos.toString('base64')+'">';
  }));
  const page = await browser.newPage();
  try {
    await page.setContent('<style>*{box-sizing:border-box}body{margin:0}main{display:inline-flex;gap:18px;padding:18px;background:#e8ebe9}</style><main>'+fotos.join('')+'</main>');
    await page.evaluate(()=>Promise.all(Array.from(document.images,img=>img.decode())));
    await page.locator('main').screenshot({path:path.join(dir,archivo),type:'jpeg',quality:93});
  } finally { await page.close(); }
}

async function ejecutar() {
  const {base,destino,verificar} = opciones(process.argv.slice(2));
  if (verificar || existsSync(destino)) {
    await verificarEntrega(destino);
    console.log('Entrega existente comprobada: ' + destino);
    return;
  }
  const texto = (await fs.readFile(path.join(base,'pie-de-foto.txt'),'utf8')).trim();
  if (!texto) throw Error('Falta el pie de foto.');
  for (const p of piezas) await fs.access(path.join(base,'arte',p.html));
  const ejecutable = buscarNavegador();
  const temporal = await fs.mkdtemp(path.join(base,'.exportacion-'));
  try {
    const publicar = path.join(temporal,'publicar');
    for (const grupo of ['carrusel','historias']) await fs.mkdir(path.join(publicar,grupo),{recursive:true});
    const browser = await chromium.launch({executablePath:ejecutable,headless:true,args:['--disable-gpu','--disable-extensions','--disable-background-networking']});
    try {
      for (const p of piezas) await exportarPieza(browser,base,p,publicar);
      await crearVista(browser,temporal,piezas.slice(0,4),vistas[0]);
      await crearVista(browser,temporal,piezas.slice(4),vistas[1]);
    } finally { await browser.close(); }
    await fs.writeFile(path.join(publicar,'pie-de-foto.txt'), texto+'\n');
    const zip = new JSZip();
    for (const nombre of [...piezas.map(p=>p.jpg),'pie-de-foto.txt']) zip.file(nombre,await fs.readFile(path.join(publicar,nombre)),{createFolders:false});
    await fs.writeFile(path.join(temporal,'instagram.zip'),await zip.generateAsync({type:'nodebuffer'}));
    await verificarEntrega(temporal);
    try { await fs.rename(temporal,destino); }
    catch (err) {
      if (!existsSync(destino)) throw err;
      await verificarEntrega(destino);
    }
    console.log('Entrega comprobada: ' + destino);
  } finally { await fs.rm(temporal,{force:true,recursive:true}); }
}
module.exports = { buscarNavegador };
if (require.main === module) {
  ejecutar().catch(e=>{console.error(e.message);process.exitCode=1;});
}
