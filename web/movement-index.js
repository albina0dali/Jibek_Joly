import model from './movement-index-model.json' with {type:'json'};
export {model as movementIndexModel};
const clamp=n=>Math.max(0,Math.min(100,n));
export function calculateMovementIndex({weightedDelaySeconds=0,averageDelaySeconds=0,utilization=0,conflicts=0,energySavingsPercent=0}){
 const scores={schedule:clamp(100-weightedDelaySeconds/model.delay_divisor_seconds),capacity:clamp(100-Math.abs(model.target_utilization-utilization)*model.utilization_penalty-conflicts*model.capacity_conflict_penalty),energy:clamp(model.energy_base+clamp(energySavingsPercent)*model.energy_saving_coefficient),conflict:clamp(100-model.conflict_penalty*conflicts),arrival:clamp(100-averageDelaySeconds/model.arrival_divisor_seconds)};
 const index=Math.round(Object.entries(scores).reduce((sum,[k,v])=>sum+v*model.weights[k]/100,0)*10)/10;
 return {index,factors:Object.values(scores).map(n=>Math.round(n*10)/10),weights:Object.values(model.weights),level:index>=model.normal_threshold?'good':index<model.attention_threshold?'bad':'warn'};
}
