import type {Snapshot,Session} from './types';

export interface PageProps {state:Snapshot;session:Session;select:(id:string)=>void;act:(path:string,body?:unknown)=>Promise<boolean>;notify:(message:string)=>void}
