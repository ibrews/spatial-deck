/* Spatial Deck frame runtime: the iframe side of the slide-module step protocol (slides/README.md § iframe modules).
   A seekable motion graphic loads this, builds its DOM synchronously from SDFrame.props(defaults), then calls
   SDFrame.init({duration, steps}). It then behaves the same three ways it always did, plus one:
     standalone (opened directly)  plays from 0 on its own CSS/WAAPI clock
     ?static / reduced motion      final frame;  ?t=SEC  the paused frame at SEC  (render_motion.mjs uses seek)
     inside a deck                 parked on the final frame until the deck sends enter, then replays from 0
   and answers the deck's enter / step / leave / seek / static messages without reloading. Animate only with CSS
   animations or WAAPI so document.getAnimations() sees everything; steps are exposed as html[data-step="n"]
   (style against it) and/or an onStep(n, instant) hook. */
(function(){
  var MSG='spatial-deck',P=new URLSearchParams(location.search),props={},inDeck=window.parent!==window;
  var m=/[#&]sdp=([^&]*)/.exec(location.hash);
  if(m){try{props=JSON.parse(decodeURIComponent(m[1]));}catch(e){console.error('sd-frame: #sdp props are not valid JSON',e);}}
  var rm=false;try{rm=matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){}
  var cfg=null,self=document.currentScript,here=self&&self.src?self.src.replace(/[^/]*$/,''):'';
  // Same look lookup as the motion recolorer: ?look=, else window.name "sd-look:<id>" (set by the deck), else the parent's.
  function lookId(){var l=P.get('look');if(!l){var n=/sd-look:([\w-]+)/.exec(window.name||'');if(n)l=n[1];}
    if(!l){try{if(inDeck)l=parent.document.body.dataset.look;}catch(e){}}return l||'noir';}
  function anims(){return document.getAnimations();}
  function seek(t){anims().forEach(function(a){a.pause();a.currentTime=t*1000;});if(cfg&&cfg.onSeek)cfg.onSeek(t);}
  function setStep(n,instant){document.documentElement.dataset.step=String(n);if(cfg&&cfg.onStep)cfg.onStep(n,!!instant);}
  function finalFrame(){setStep(cfg.steps,true);seek(cfg.duration);}
  function play(){setStep(0,true);if(cfg.onEnter)cfg.onEnter();anims().forEach(function(a){a.currentTime=0;a.play();});}
  window.SDFrame={
    // Defaults merged with the deck's props (shallow, like the deck): the frame must build from these before init().
    props:function(defaults){var o={},k;for(k in defaults||{})o[k]=defaults[k];for(k in props)o[k]=props[k];return o;},
    init:function(c){
      cfg={duration:+c.duration||0,steps:Math.max(0,c.steps|0),onEnter:c.onEnter,onStep:c.onStep,onLeave:c.onLeave,onSeek:c.onSeek};
      window.MOTION_END=cfg.duration;window.seek=seek;window.SDFrame.config=cfg;
      // A non-noir look recolors the frame with slides/look.js (written by tools/apply_look.py). document.write keeps it
      // synchronous: it runs right after the frame's build script, before anything is captured.
      if(lookId()!=='noir'&&document.readyState==='loading')document.write('<script src="'+here+'look.js"><\/script>');
      if(rm||P.has('static'))finalFrame();
      else if(P.has('t'))seek(+P.get('t'));
      else if(inDeck)finalFrame();  // parked, so thumbnails and an un-entered slide show the finished graphic
      else setStep(0,true);
      if(inDeck)parent.postMessage({sd:MSG,v:1,type:'ready',steps:cfg.steps,duration:cfg.duration},'*');
    }
  };
  addEventListener('message',function(e){
    var d=e.data;if(!d||d.sd!==MSG||!cfg||e.source!==window.parent)return;
    var instant=!!d.instant||rm;
    if(d.type==='enter'){if(instant){setStep(0,true);seek(cfg.duration);}else play();}
    else if(d.type==='step')setStep(d.n|0,instant);
    else if(d.type==='leave'){if(cfg.onLeave)cfg.onLeave();finalFrame();}
    else if(d.type==='seek')seek(+d.t||0);
    else if(d.type==='static')finalFrame();
  });
})();
