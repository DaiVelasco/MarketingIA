// Reproduce el archivo con Chromium y comprueba que decodifica imagen en movimiento.
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const { chromium } = require('playwright-core');
const { buscarNavegador } = require('./exportar.cjs');

async function comprobar(browser, file) {
  const page = await browser.newPage();
  try {
    await page.goto(pathToFileURL(path.resolve(file)).href, {waitUntil:'load'});
    const video = page.locator('video').first();
    await video.waitFor();
    await page.waitForFunction(() => document.querySelector('video')?.readyState >= 2, null, {timeout:15000});
    const result = await video.evaluate(async el => {
      el.muted = true;
      const progress = () => new Promise((resolve, reject) => {
        const started = el.currentTime;
        const timer = setTimeout(() => {clearInterval(interval); reject(Error('Imagen detenida'));}, 6000);
        const interval = setInterval(() => {
          if (el.currentTime - started < 0.14) return;
          clearInterval(interval);
          clearTimeout(timer);
          resolve();
        }, 50);
      });
      await el.play();
      const samples = [];
      for (const t of [0, el.duration / 2, Math.max(0, el.duration - 0.7)]) {
        if (t > 0) {
          const seeked = new Promise(resolve => el.addEventListener('seeked', resolve, {once:true}));
          el.currentTime = t;
          await seeked;
        }
        await progress();
        samples.push(Number(el.currentTime.toFixed(2)));
      }
      el.pause();
      const frames = el.getVideoPlaybackQuality().totalVideoFrames;
      if (!el.videoWidth || frames < 3 || el.error) throw Error('Decodificación incompleta.');
      return {duracion:el.duration, ancho:el.videoWidth, alto:el.videoHeight, muestras:samples, fotogramas:frames};
    }, undefined, {timeout:20000});
    console.log(JSON.stringify({archivo:path.basename(file), ...result}));
  } finally { await page.close(); }
}

async function main(files) {
  if (!files.length) throw Error('Indica al menos un MP4 o reproductor HTML.');
  const browser = await chromium.launch({executablePath:buscarNavegador(), headless:true,
    args:['--autoplay-policy=no-user-gesture-required', '--disable-background-networking']});
  try {
    for (const file of files) await comprobar(browser, file);
  } finally { await browser.close(); }
}
main(process.argv.slice(2)).catch(err => { console.error(err.message); process.exitCode = 1; });
