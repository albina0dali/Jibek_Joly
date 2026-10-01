import {ecoAdvice} from '../web/eco-model.js';

const fields={distance_km:[0,200],current_speed_kmh:[0,200],speed_limit_kmh:[Number.MIN_VALUE,200],now_min:[0,500],mass_tons:[Number.MIN_VALUE,20000]};
export const ecoAssumptions=[
 'Synthetic freight acceleration 0.10 m/s² and deceleration 0.12 m/s²; not validated braking curves.',
 'Energy proxy is not measured diesel consumption.',
 'A red signal takes priority over advisory speed.'
];
export function adviceFromSnapshot(input){
 const invalid=()=>{throw Object.assign(Error('Invalid Eco snapshot'),{status:422});};
 if(!input||Array.isArray(input)||typeof input!=='object'||typeof input.train_id!=='string'||!input.train_id.startsWith('SIM-')||input.train_id.length>100)invalid();
 const values={...input,mass_tons:input.mass_tons??1000};
 for(const [key,[min,max]] of Object.entries(fields))if(!Number.isFinite(values[key])||values[key]<min||values[key]>max)invalid();
 const open=input.signal_open_min??null;
 if(open!==null&&(!Number.isFinite(open)||open< -1||open>600))invalid();
 const advice=ecoAdvice({distanceKm:values.distance_km,currentKmh:values.current_speed_kmh,capKmh:values.speed_limit_kmh,nowMin:values.now_min,openMin:open,massTons:values.mass_tons});
 return {train_id:input.train_id,...advice,assumptions:ecoAssumptions};
}
export const ecoRequestSchema={type:'object',required:['train_id','distance_km','current_speed_kmh','speed_limit_kmh','now_min'],properties:{train_id:{type:'string',pattern:'^SIM-'},...Object.fromEntries(Object.entries(fields).map(([key,[min,max]])=>[key,{type:'number',minimum:min,maximum:max}])),signal_open_min:{type:'number',nullable:true,minimum:-1,maximum:600}}};
export const ecoPaths={
 '/eco/advice':{post:{summary:'Synthetic smooth target-time advice from the supplied snapshot only',requestBody:{required:true,content:{'application/json':{schema:{$ref:'#/components/schemas/EcoRequest'}}}},responses:{200:{description:'Computed speed profile and energy proxy; advisory only'},422:{description:'Invalid simulation inputs'}}}},
 '/eco/package':{get:{summary:'Kazakhstan-only synthetic train and signal package',responses:{200:{description:'Compressed demonstration input; not operational ҚТЖ data'}}}}
};
