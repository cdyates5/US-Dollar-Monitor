<script>
(function(){
  function charts(){var o=[];document.querySelectorAll('canvas').forEach(function(c){var ch=window.Chart&&Chart.getChart?Chart.getChart(c):null;if(ch)o.push(ch);});return o;}
  function firstNonNull(ds){for(var i=0;i<ds.length;i++){var d=ds[i].data||[];for(var j=0;j<d.length;j++){if(d[j]!==null&&d[j]!==undefined)return d[j];}}return null;}
  function isXY(ch){var f=firstNonNull(ch.data.datasets||[]);return f!==null&&typeof f==='object'&&('x' in f);}
  function pickMain(chs){var best=null,bs=-1;chs.forEach(function(ch){var ds=ch.data.datasets||[];var ml=0,ls=0;ds.forEach(function(d){var n=(d.data||[]).length;if(n>ml)ml=n;if(n>=24)ls++;});var hl=(ch.data.labels||[]).length>=24;if(!hl&&!isXY(ch))return;var sc=ml*10+ls*100-(ds.length>6?200:0);if(sc>bs){bs=sc;best=ch;}});return best;}
  function fx(x){if(typeof x==='number'){var y=Math.floor(x+1e-6),fr=x-y,mo=Math.round(fr*12)+1;if(mo<1)mo=1;if(mo>12){y++;mo=1;}return y+'-'+String(mo).padStart(2,'0');}return x;}
  function toCSV(ch){var ds=ch.data.datasets||[],lb=ch.data.labels||[],xy=isXY(ch);
    var nm=ds.map(function(d,i){return (d.label&&d.label.trim())?d.label.replace(/[",\n]/g,' ').trim():('series'+(i+1));});var rows=[];
    if(xy){var mp={};ds.forEach(function(d,di){(d.data||[]).forEach(function(p){if(p==null||typeof p!=='object')return;var xk=fx(p.x);if(!mp[xk])mp[xk]={};mp[xk][di]=(p.y==null?'':p.y);});});
      var ks=Object.keys(mp).sort();rows.push(['x'].concat(nm).join(','));ks.forEach(function(k){var r=[k];for(var i=0;i<ds.length;i++)r.push((k in mp&&mp[k][i]!=null)?mp[k][i]:'');rows.push(r.join(','));});}
    else{rows.push(['date'].concat(nm).join(','));for(var i=0;i<lb.length;i++){var r=[String(lb[i]).replace(/[",\n]/g,' ')];ds.forEach(function(d){var v=(d.data||[])[i];r.push(v==null?'':v);});rows.push(r.join(','));}}
    return rows.join('\n');}
  window.__exportCSV=function(){var m=pickMain(charts());return m?toCSV(m):null;};
  function ping(){try{parent.postMessage({__csvready:true,id:window.frameElement?window.frameElement.id:null},'*');}catch(e){}}
  window.addEventListener('load',function(){setTimeout(ping,800);});
})();
</script>
