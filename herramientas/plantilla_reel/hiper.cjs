const fs=require("node:fs");
const path=require("node:path");
const {pathToFileURL}=require("node:url");
const {createRequire}=require("node:module");
async function main(){
  const [project,destination,n]=process.argv.slice(2);
  const libs=process.env.PLAYWRIGHT_NODE_MODULES;
  const get=libs?createRequire(path.resolve(libs,"../package.json")):require;
  const {chromium}=get("playwright-core");
  const executablePath=process.env.MARKETING_BROWSER||["C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe","/usr/bin/google-chrome","/usr/bin/chromium"].find(fs.existsSync);
  const browser=await chromium.launch({headless:true,executablePath});
  try {
    const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.join(project,"index.html")).href);
    for(let f=0;f<Number(n);f++){
      await page.evaluate(f=>window.fotograma(f),f);
      await page.screenshot({type:"jpeg",quality:95,path:path.join(destination,String(f).padStart(3,"0")+".jpg")});
    }
  } finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
