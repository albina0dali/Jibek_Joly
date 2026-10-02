import {spawnSync} from 'node:child_process';
import path from 'node:path';
const python=process.env.EXTENSION_PYTHON||path.resolve(process.platform==='win32'?'.jol-local/extension-venv/Scripts/python.exe':'.jol-local/extension-venv/bin/python');
const result=spawnSync(python,['-m','pytest','tests/test_extension.py','-q','-s','-p','no:cacheprovider'],{stdio:'inherit',windowsHide:true});
if(result.error)console.error(result.error.message);
process.exitCode=result.status??1;
