import React from 'react';
import {AbsoluteFill, Composition, continueRender, delayRender, registerRoot, staticFile, useCurrentFrame} from 'remotion';

const fonts=delayRender('Tipografías del pronóstico');
Promise.all([['Archivo','ArchivoBlack.ttf'],['Grotesk','SpaceGrotesk.ttf']].map(async ([family,file])=>{
  const face=new FontFace(family,'url('+staticFile(file)+')');
  document.fonts.add(await face.load());
})).then(()=>continueRender(fonts),e=>{throw e;});

const paper='#f7f4e8', green='#92f6b5', field='#102c29', dark='#14362e';
const clamp=n=>Math.min(1,Math.max(0,n));
const ease=n=>{const t=clamp(n);return t*t*(3-2*t);};

function Rain({f}) {
  return <g fill="none" stroke={green} strokeWidth="4.5" strokeLinecap="round">
    {[0,1,2,3,4,5].map((i)=>{
      const p=((f+5*i)%18+18)%18/18;
      return <path key={i} opacity={Math.sin(Math.PI*p)*.95}
        d={'M '+(180+i*12-7*p)+' '+(115+p*22)+' l -3 7'}/>;
    })}
  </g>;
}

function Radar(){
  const f=useCurrentFrame();
  const arrival=ease(f/7);
  const op=arrival*(1-ease((f-79)/10));
  const cloudX=15*(1-ease(f/13))+Math.sin(f*.065)*2.2;
  const carY=Math.sin(f*.29)*.6;
  return <AbsoluteFill><svg width="428" height="236" viewBox="0 0 428 236">
    <g opacity={op} transform={'translate(0 '+Math.round(8*(1-arrival))+')'}>
      <rect x="7" y="11" width="407" height="211" rx="26" fill="#081d1b" opacity=".42"/>
      <rect x="4" y="5" width="407" height="211" rx="26" fill={field}/>
      <rect x="5" y="6" width="405" height="209" rx="25" fill="none" stroke="#6c9c8a" strokeWidth="2" opacity=".75"/>
      <circle cx="29" cy="34" r="5" fill={green}/>
      <text x="45" y="43" fill={paper} fontSize="26" letterSpacing="2.2" fontFamily="Grotesk" fontWeight="700">RADAR</text>
      <path d="M 18 58 H 392" stroke="#648e83" strokeWidth="1.4"/>
      <g fill="#a2c3af" opacity=".5">{[0,1,2].map(i=><rect key={i} x={354+i*10} y={35-i*4} width="5" height={5+i*4}/>)}</g>
      <path d="M 28 173 H 387 M 60 159 v 22 M 116 159 v 22 M 301 159 v 22 M 354 159 v 22" fill="none" stroke="#486960" strokeWidth="2.5"/>
      <g transform={'translate('+cloudX+' 0)'} fill="#e8efdf">
        <path d="M 171 115 c-11 0-17-7-17-15 0-9 7-16 17-16 2-14 14-22 28-20 11 0 20 6 24 15 11-4 24 1 28 12 8 0 14 5 14 12 0 7-6 12-14 12 Z"/>
      </g>
      <Rain f={f}/>
      <g transform={'translate(0 '+carY+')'} stroke={green} strokeWidth="3.4" strokeLinejoin="round" fill="#285444">
        <path d="M 153 169 v-12 l14-3 13-15 h41 l17 14 17 4 v12 Z"/>
        <path d="M 182 142 l-9 10 h28 v-10 Z M 207 142 v10 h23 l-11-10 Z" fill={dark} strokeWidth="2"/>
        <circle cx="172" cy="169" r="7" fill={field}/><circle cx="237" cy="169" r="7" fill={field}/>
      </g>
      <path d="M154 190 v5 h101 v-5" fill="none" stroke="#bbdcca" strokeWidth="2.5"/>
    </g></svg></AbsoluteFill>;
}

function Share(){
  const f=useCurrentFrame();
  const pop=ease(f/7), leave=1-ease((f-62)/6);
  const drift=7*(1-ease((f-1)/8));
  return <AbsoluteFill><svg width="920" height="230" viewBox="0 0 920 230">
    <g opacity={Math.max(.65,pop)*leave} transform={'translate(0 '+Math.round(7*(1-pop))+')'}>
      <rect x="8" y="15" width="886" height="194" rx="28" fill="#0b1815" opacity=".62"/>
      <rect x="5" y="8" width="886" height="194" rx="28" fill={dark}/>
      <rect x="7" y="10" width="882" height="190" rx="26" stroke="#7ba993" strokeWidth="2" fill="none"/>
      <g transform={'translate('+(45-drift)+' '+(53+drift)+')'} stroke={green} strokeLinejoin="round" strokeWidth="5" fill="none">
        <path d="M 7 45 L 105 8 L 76 94 L 50 65 L 30 78 L 31 56 Z"/>
        <path d="M 31 56 L 105 8 L 49 65"/>
      </g>
      <text x="187" y="87" fill={green} fontFamily="Grotesk" fontWeight="650" fontSize="55" letterSpacing="-1.6">Mándaselo a</text>
      <text x="183" y="159" fill={paper} fontFamily="Archivo" fontSize="78" letterSpacing="-2.7">tu copiloto</text>
    </g></svg></AbsoluteFill>;
}

function Root(){return <>
  <Composition id="RadarCabina" component={Radar} durationInFrames={90} fps={30} width={428} height={236}/>
  <Composition id="Copiloto" component={Share} durationInFrames={68} fps={30} width={920} height={230}/>
</>;}
registerRoot(Root);
