// Same-origin namespace; the Python solver is an optional separate service.
export async function extensionProxy(req,env){
 const url=new URL(req.url);
 if(!req.headers.get('oai-authenticated-user-id'))return Response.json({detail:'Войдите через ChatGPT'},{status:401});
 if(req.method!=='GET'&&req.headers.get('origin')!==url.origin)return Response.json({detail:'Same-origin requests only'},{status:403});
 if(!env.EXTENSION_URL)return Response.json({detail:'Сервис расширения не подключён. Настройте EXTENSION_URL; для локального запуска используйте npm start.'},{status:503});
 const path=url.pathname.slice('/api/extension'.length);
 if(!/^\/(session|state|history|quality|incidents|replan(?:\/[^/]+\/apply)?|simulation\/(pause|resume|reset|1|2|5)|reports\/(csv|pdf)|resources\/yard(?:\/(optimize|apply))?)$/.test(path))return Response.json({detail:'Unknown extension endpoint'},{status:404});
 const base=new URL(env.EXTENSION_URL);
 const headers=new Headers({'Content-Type':'application/json'});
 if(env.EXTENSION_SERVICE_KEY)headers.set('X-Extension-Key',env.EXTENSION_SERVICE_KEY);
 let method=req.method,body;
 if(path==='/session'){
  if(method!=='POST')return new Response(null,{status:405});
  // Existing team identity grants access; never expose service passwords in UI.
  body=JSON.stringify({username:'dispatcher',password:env.EXTENSION_DISPATCH_PASSWORD||'dispatch-demo'});
 }else{
  const token=req.headers.get('authorization');if(token)headers.set('Authorization',token);
  if(!['GET','HEAD'].includes(method))body=await req.text();
 }
 const target=new URL(path==='/session'?'/api/auth/login':'/api'+path,base);target.search=url.search;
 try{
  const upstream=new Request(target,{method,headers,body,redirect:'manual'});
  const response=await (env.EXTENSION_SERVICE?env.EXTENSION_SERVICE.fetch(upstream):fetch(upstream));
  if(response.status>=300&&response.status<400)throw Error('Unexpected upstream redirect');
  const out=new Headers(response.headers);out.set('Cache-Control','no-store');
  return new Response(response.body,{status:response.status,headers:out});
 }catch(error){console.error('Extension upstream unavailable:',error.message);return Response.json({detail:'Сервис расширения недоступен. Проверьте запуск Python backend.'},{status:503});}
}
