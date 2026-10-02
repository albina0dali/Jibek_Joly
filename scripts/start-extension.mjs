import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
export function startExtension(){
 if(process.env.EXTENSION_URL)return {url:process.env.EXTENSION_URL,stop(){}};
 const python=process.env.EXTENSION_PYTHON||path.resolve(process.platform==='win32'?'.jol-local/extension-venv/Scripts/python.exe':'.jol-local/extension-venv/bin/python');
 if(!fs.existsSync(python)){
  console.warn('Extension unavailable: create .jol-local/extension-venv and install server/extension/requirements.lock.txt. Core pages remain available.');
  return {url:'',stop(){}};
 }
 fs.mkdirSync('.jol-local',{recursive:true});
 const child=spawn(python,['-m','uvicorn','main:app','--app-dir','server/extension','--host','127.0.0.1','--port','8001'],{stdio:'inherit',windowsHide:true,env:{...process.env,DATABASE_PATH:path.resolve('.jol-local/extension.sqlite')}});
 child.on('error',error=>console.error('Extension backend:',error.message));
 return {url:'http://127.0.0.1:8001',stop(){child.kill()}};
}
