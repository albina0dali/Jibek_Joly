import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
export default defineConfig({plugins:[react()],resolve:{dedupe:['react','react-dom'],alias:Object.fromEntries(['react','react-dom','react-router-dom','lucide-react'].map(name=>[name,path.resolve('node_modules',name)]))},server:{fs:{allow:[path.resolve('..','..','..')]},proxy:{'/api':'http://127.0.0.1:8001','/ws':{target:'ws://127.0.0.1:8001',ws:true},'/health':'http://127.0.0.1:8001'}}});
