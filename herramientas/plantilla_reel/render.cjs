const fs = require("node:fs");
const path = require("node:path");
const {createRequire} = require("node:module");

async function render() {
  const [assets, out, propsFile, scratch] = process.argv.slice(2);
  const libs = process.env.REMOTION_NODE_MODULES || path.join(__dirname,"node_modules");
  const load = createRequire(path.resolve(libs,"../package.json"));
  const {bundle} = load("@remotion/bundler");
  const {selectComposition,renderMedia} = load("@remotion/renderer");
  const serveUrl = await bundle({entryPoint:path.join(__dirname,"Reel.jsx"),publicDir:assets,
    outDir:path.join(scratch,"bundle"),enableCaching:false,
    webpackOverride:config => ({...config,resolve:{...config.resolve,modules:[libs,...(config.resolve.modules || ["node_modules"])]}})});
  const inputProps = JSON.parse(fs.readFileSync(propsFile,"utf8"));
  const options = {serveUrl,inputProps,logLevel:"error"};
  const browser = process.env.MARKETING_BROWSER || [
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium"
  ].find(fs.existsSync);
  if (browser) options.browserExecutable = browser;
  const composition = await selectComposition({...options,id:"ReelVertical"});
  let bucket = -1;
  const concurrency = Number(process.env.REEL_CONCURRENCIA || 2);
  if (!Number.isInteger(concurrency) || concurrency < 1) throw new Error("REEL_CONCURRENCIA debe ser un entero positivo.");
  await renderMedia({...options,composition,outputLocation:out,codec:"h264",crf:18,muted:true,
    imageFormat:"jpeg",jpegQuality:95,pixelFormat:"yuv420p",concurrency,overwrite:true,
    onProgress:({progress})=>{
      const value = Math.floor(progress*10);
      if(value>bucket){bucket=value; console.log("Remotion " + (value*10) + "%");}
    }});
}
render().catch(err=>{console.error(err);process.exitCode=1;});
