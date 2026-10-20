let seconds=300;const timer=document.getElementById("timer");const form=document.getElementById("quizForm");
if(timer&&form){const tick=()=>{let m=Math.floor(seconds/60),s=seconds%60;timer.textContent=String(m).padStart(2,"0")+":"+String(s).padStart(2,"0");if(seconds<=0)form.submit();else seconds--};tick();setInterval(tick,1000);}
