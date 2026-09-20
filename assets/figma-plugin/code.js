figma.showUI(__html__, {width:420,height:360});
let busy=false;
function validate(p){
  if(!p||p.schemaVersion!==1||typeof p.snapshotId!=='string'||p.snapshotId.length>20000||!Array.isArray(p.items)||!p.items.length||p.items.length>30)throw Error('无效确认包');
  for(const key of ['project','revision'])if(typeof p[key]!=='string'||p[key].length>200)throw Error('无效项目字段');
  for(const i of p.items){
    for(const k of ['id','version','title','palette','concept','changes','sourceSha256'])if(typeof i[k]!=='string'||!i[k]||i[k].length>10000)throw Error('缺少/过长字段：'+k);
    if(!i.approval?.by||!i.approval?.at||i.approval.version!==i.version)throw Error('缺少对应版本确认');
    for(const k of ['logo','phone'])if(typeof i[k]!=='string'||!i[k].startsWith('data:image/png;base64,')||i[k].length>24*1024*1024)throw Error('无效 PNG：'+k);
    if(!Number.isFinite(i.phoneWidth)||!Number.isFinite(i.phoneHeight)||i.phoneWidth<100||i.phoneWidth>2000||i.phoneHeight<100||i.phoneHeight>3000)throw Error('无效手机尺寸');
  }
}
function decode(uri){const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',s=uri.split(',')[1];if(!/^[A-Za-z0-9+/]*={0,2}$/.test(s)||s.length%4)throw Error('无效 Base64');const bytes=[];let value=0,bits=0;for(const ch of s){if(ch==='=')break;value=(value<<6)|alphabet.indexOf(ch);bits+=6;if(bits>=8){bits-=8;bytes.push((value>>bits)&255)}}return new Uint8Array(bytes)}
figma.ui.onmessage=async m=>{
  if(m.type!=='import'||busy)return;busy=true;let board;
  try{
    const p=m.payload;validate(p);
    const existing=figma.currentPage.children.find(n=>n.getPluginData('logoReviewSnapshot')===p.snapshotId);
    if(existing){figma.viewport.scrollAndZoomIntoView([existing]);figma.ui.postMessage({message:'此快照已导入，已定位评审板：'+existing.id});return}
    const fonts=await figma.listAvailableFontsAsync();const font=fonts.find(f=>f.fontName.family==='Noto Sans SC'&&f.fontName.style==='Regular')?.fontName||fonts.find(f=>f.fontName.family==='Inter'&&f.fontName.style==='Regular')?.fontName;
    if(!font)throw Error('缺少可用的 Noto Sans SC / Inter Regular 字体');await figma.loadFontAsync(font);
    const prepared=p.items.map(i=>({i,logo:figma.createImage(decode(i.logo)),phone:figma.createImage(decode(i.phone))}));
    const fill={type:'SOLID',color:{r:.96,g:.97,b:.99}};
    function frame(parent,name){const f=figma.createFrame();f.name=name;f.layoutMode='VERTICAL';f.primaryAxisSizingMode='AUTO';f.counterAxisSizingMode='FIXED';f.resize(960,100);f.paddingTop=f.paddingBottom=f.paddingLeft=f.paddingRight=24;f.itemSpacing=16;f.fills=[fill];if(parent)parent.appendChild(f);return f}
    function text(parent,str,size){const t=figma.createText();parent.appendChild(t);t.fontName=font;t.fontSize=size;t.characters=str;t.resize(900,20);t.textAutoResize='HEIGHT';t.fills=[{type:'SOLID',color:{r:.08,g:.1,b:.15}}];return t}
    function picture(parent,name,hash,w,h){const r=figma.createRectangle();parent.appendChild(r);r.name=name;r.resize(w,h);r.fills=[{type:'IMAGE',imageHash:hash,scaleMode:'FIT'}];return r}
    board=frame(null,p.project+' / '+p.revision);board.x=Math.max(figma.viewport.center.x,...figma.currentPage.children.filter(n=>n!==board).map(n=>n.x+n.width+80));board.y=figma.viewport.center.y;text(board,p.project+' · 确认方案',28);
    for(const {i,logo,phone} of prepared){const section=frame(board,i.id+' / '+i.version+' / '+i.palette);text(section,i.title+' · '+i.palette,24);text(section,i.concept,16);text(section,'本轮修改：'+i.changes,16);const pair=frame(section,'Logo 与手机主屏');pair.layoutMode='HORIZONTAL';pair.paddingLeft=pair.paddingRight=0;pair.itemSpacing=40;picture(pair,'Logo / raster',logo.hash,420,420);picture(pair,'手机主屏 / raster',phone.hash,280,280*i.phoneHeight/i.phoneWidth);text(section,'确认：'+i.approval.by+' / '+i.approval.at+'；源 SHA256：'+i.sourceSha256,12)}
    board.setPluginData('logoReviewSnapshot',p.snapshotId);figma.currentPage.selection=[board];figma.viewport.scrollAndZoomIntoView([board]);figma.ui.postMessage({message:'导入完成：'+p.items.length+' 个方案；评审板节点 '+board.id+'。请检查文字、配色与手机效果。'});
  }catch(e){if(board)board.remove();figma.ui.postMessage({message:'导入失败：'+e.message+'。本次新建板已撤回，既有内容未改动。'})}finally{busy=false}
};
