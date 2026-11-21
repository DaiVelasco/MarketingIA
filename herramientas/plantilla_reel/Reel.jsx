import React from "react";
import {AbsoluteFill,Composition,Img,interpolate,registerRoot,staticFile,useCurrentFrame} from "remotion";

const clamp={extrapolateLeft:"clamp",extrapolateRight:"clamp"};
const font='"Arial","Segoe UI",sans-serif';
const jpg=(name,f)=>staticFile(name+"/"+String(Math.max(0,Math.floor(f))).padStart(3,"0")+".jpg");

function Subtitulo({cues,frame}) {
  const cue=cues.find(c=>frame/30>=c.inicio&&frame/30<c.fin);
  if(!cue) return null;
  return <div style={{position:"absolute",bottom:397,left:100,right:100,color:"#fff",
    textAlign:"center",fontFamily:font,fontSize:57,fontWeight:550,lineHeight:"58px",letterSpacing:-1.35,
    whiteSpace:"pre-line",WebkitTextStroke:"0.6px rgba(20,20,20,.46)",
    textShadow:"0 3px 4px rgba(0,0,0,.94),0 0 10px rgba(0,0,0,.69),0 1px 17px rgba(0,0,0,.65)"}}>
    {cue.texto}</div>;
}

function Origen({shot,f,style}) {
  if(shot.placa) {
    return <AbsoluteFill style={{backgroundColor:"#fff",display:"flex",alignItems:"center",justifyContent:"center",...style}}>
      <Img src={staticFile(shot.firma)} style={{width:657,maxHeight:280,objectFit:"contain"}}/>
    </AbsoluteFill>;
  }
  return <AbsoluteFill style={style}><Img src={jpg(shot.carpeta,f)}
    style={{width:"100%",height:"100%",objectFit:"cover"}}/></AbsoluteFill>;
}

function Film({planos,subtitulos,tinta}) {
  const frame=useCurrentFrame();
  const idx=planos.findIndex(p=>frame>=p.f0 && frame<p.f1);
  if(idx<0) return <AbsoluteFill style={{backgroundColor:"white"}}/>;
  const shot=planos[idx], local=frame-shot.f0, previous=idx>0?planos[idx-1]:null;
  const dissolve=shot.fundido||0;
  const mix=dissolve>0?interpolate(local,[0,dissolve],[0,1],clamp):1;
  return <AbsoluteFill style={{backgroundColor:shot.placa?"white":"#161918"}}>
    {previous&&mix<1&&<Origen shot={previous} f={previous.f1-previous.f0-1}/>}
    <Origen shot={shot} f={local} style={{opacity:mix}}/>
    {tinta&&frame>=tinta.frame&&frame<tinta.frame+24&&<Img src={staticFile("tinta/s"+String(frame-tinta.frame).padStart(2,"0")+".png")}
      style={{position:"absolute",left:tinta.x,top:tinta.y,width:tinta.ancho,height:tinta.alto,opacity:tinta.opacidad,transform:"rotate("+tinta.giro+"deg)"}}/>}
    <Subtitulo cues={subtitulos} frame={frame}/>
  </AbsoluteFill>;
}
registerRoot(()=><Composition id="ReelVertical" component={Film} durationInFrames={600} fps={30}
  width={1080} height={1920} defaultProps={{fotogramas:600,planos:[],subtitulos:[],tinta:null}}
  calculateMetadata={({props})=>({durationInFrames:props.fotogramas})}/>);
