import React from "react";
import {AbsoluteFill, Composition, continueRender, delayRender, registerRoot, staticFile, useCurrentFrame} from "remotion";
import anchors from "./encuadres.json";

const loading = delayRender("Tipografía del juego");
Promise.all([["Archivo","ArchivoBlack.ttf"],["Grotesk","SpaceGrotesk.ttf"]].map(async ([family,file])=>{
  const face=new FontFace(family,`url("${staticFile(file)}")`);
  document.fonts.add(await face.load());
})).then(()=>continueRender(loading),e=>{console.error(e);continueRender(loading);});

const ink="#101914", white="#f8f9f3", mint="#76ffa4";
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>{const t=clamp(x);return t*t*(3-2*t);};
const mix=(a,b,t)=>a+(b-a)*t;
const slots=[{x:723,y:182},{x:813,y:182},{x:903,y:182}];
const cues=[
  {a:57,b:114,label:"El faro",contour:"M 42 900 Q 275 625 550 494 Q 784 350 953 48 Q 894 452 797 675 Q 592 873 42 900 Z"},
  {a:114,b:171,label:"La pantalla",contour:"M 68 82 Q 74 54 107 54 L 938 108 Q 961 109 951 146 L 833 934 Q 829 957 797 951 L 112 801 Q 81 797 77 757 Z"},
  {a:171,b:228,label:"La palanca",contour:"M 50 940 Q 256 706 382 371 Q 412 221 526 142 Q 675 39 841 119 Q 954 162 966 305 Q 958 453 803 456 Q 685 425 612 514 Q 538 625 362 900"}
];
const geometry=(i,p)=>{
  const keys=anchors[i].positions, time=clamp(p)*(keys.length-1);
  const a=keys[Math.floor(time)], b=keys[Math.min(keys.length-1,Math.ceil(time))];
  return a.map((val,j)=>mix(val,b[j],time-Math.floor(time)));
};

function Outline({index,box,progress=1,opacity=1,small=false}) {
  const [x,y,w,h]=box;
  const curve=anchors[index].path || cues[index].contour;
  const [left,top,width,height]=anchors[index].sourceBox;
  return <g transform={`translate(${x-w/2} ${y-h/2}) scale(${w/width} ${h/height}) translate(${-left} ${-top})`} opacity={opacity}>
    <path d={curve} pathLength="1" strokeDasharray="1.001 1.001" strokeDashoffset={1-progress} stroke={small?mint:ink} strokeWidth={small?3:10} vectorEffect="non-scaling-stroke" fill="none" strokeLinejoin="round" strokeLinecap="round"/>
    {!small && <path d={curve} pathLength="1" strokeDasharray="1.001 1.001" strokeDashoffset={1-progress} stroke={mint} strokeWidth="4.6" vectorEffect="non-scaling-stroke" fill="none" strokeLinejoin="round" strokeLinecap="round"/>}
  </g>;
}
function Rail({f}) {
  return <g>{slots.map((s,i)=>{
    const done=f>=cues[i].b, active=f>=cues[i].a && !done;
    return <g key={i}>
      <rect x={s.x-37} y={s.y-27} rx="12" width="74" height="54" stroke={active?mint:"#73867e"} strokeWidth={active?3:1.7} fill="#132019" fillOpacity=".9"/>
      {done ? <Outline index={i} small box={[s.x,s.y,43,32]}/> :
        <text x={s.x} y={s.y+9} textAnchor="middle" fontFamily="Grotesk" fontSize="26" fontWeight="bold" fill={active?mint:"#ccdbd0"}>{String(i+1).padStart(2,"0")}</text>}
    </g>;
  })}</g>;
}
function Label({children,y=193}) {
  return <g><rect x="74" y={y-28} width="8" height="30" fill={mint}/><text x="101" y={y-2} fontSize="30" letterSpacing="3" fontFamily="Grotesk" fontWeight="bold" fill={mint}>{children}</text></g>;
}
function Line({text,y,size=104,x=74}) {
  return <text x={x} y={y} fill={white} fontFamily="Archivo" fontSize={size} letterSpacing="-4">{text}</text>;
}
function Game() {
  const f=useCurrentFrame();
  const index=cues.findIndex(c=>f>=c.a && f<c.b);
  const cue=cues[index];
  const tail=1-ease((f-330)/6);
  let activeOutline=null;
  if(cue) {
    const l=f-cue.a, box=geometry(index,l/(cue.b-cue.a-1));
    const dock=ease((l-39)/15), s=slots[index];
    const target=[s.x,s.y,44,32];
    const b=box.map((n,i)=>mix(n,target[i],dock));
    activeOutline=<Outline index={index} box={b} progress={ease((l-1)/22)} opacity={ease(l/5)} small={dock>.85}/>;
  }
  return <AbsoluteFill style={{backgroundColor:"transparent",opacity:tail}}>
    <svg width="1080" height="1920" viewBox="0 0 1080 1920">
      <defs>
        <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop offset="0%" stopColor="#06110b" stopOpacity=".94"/><stop offset="48%" stopColor="#09150e" stopOpacity=".80"/><stop offset="100%" stopColor="#0c160f" stopOpacity="0"/></linearGradient>
      </defs>
      <rect width="1080" height={f<57?640:f>=273?590:470} fill="url(#shade)"/>
      <Rail f={f}/>
      {f<57 && <g>
        <Label>TRES PISTAS</Label>
        <g transform={`translate(0,${14*(1-ease(f/7))})`}>
          <Line text="¿DE QUÉ" y={332} size={125}/><Line text="MARCA ES?" y={455} size={125}/>
        </g>
      </g>}
      {cue && <g><Label>{`PISTA 0${index+1} / 03`}</Label><g transform={`translate(${18*(1-ease((f-cue.a)/6))},0)`}><Line text={cue.label} y={322} size={101}/></g></g>}
      {activeOutline}
      {f>=228 && f<273 && <g>
        <Label>LA MARCA</Label>
        <g opacity={ease((f-228)/5)} transform={`translate(${-24*(1-ease((f-228)/7))},0)`}><Line text="SUZUKI" y={337} size={129}/></g>
        <rect x="77" y="368" width={265*ease((f-228)/12)} height="7" rx="3" fill={mint}/>
      </g>}
      {f>=273 && <g><Label>TE TOCA</Label><Line text="¿En cuál pista" y={323} size={89}/><Line text="la sacaste?" y={417} size={89}/></g>}
    </svg>
  </AbsoluteFill>;
}
const Root=()=> <Composition id="TresPistas" component={Game} durationInFrames={336} fps={30} width={1080} height={1920}/>;
registerRoot(Root);
