const operation=(summary)=>({summary,responses:{200:{description:'Synthetic extension response; times are seconds after 08:00'},401:{description:'Team sign-in and extension Bearer session required'},409:{description:'Stale or infeasible plan'},503:{description:'Extension solver service unavailable'}}});
export const extensionPaths={
 '/api/extension/incidents':{post:operation('Inject a synthetic incident into the extension simulator')},
 '/api/extension/session':{post:operation('Create extension session using the existing team identity')},
 '/api/extension/state':{get:operation('Extension traffic snapshot; separate from core world')},
 '/api/extension/quality':{get:operation('Dynamic extension Quality Index; not the core movement index')},
 '/api/extension/replan':{post:operation('Generate three validated options without applying')},
 '/api/extension/replan/{id}/apply':{post:{...operation('Validate revision and current occupations, then apply'),parameters:[{name:'id',in:'path',required:true,schema:{type:'string'}}]}},
 '/api/extension/history':{get:{...operation('Retained snapshots and action log, or snapshot at scenario second'),parameters:[{name:'at',in:'query',schema:{type:'integer'}}]}},
 '/api/extension/reports/csv':{get:operation('Download current LIVE traffic CSV, including during replay')},
 '/api/extension/reports/pdf':{get:operation('Download current LIVE traffic PDF, including during replay')},
 '/api/extension/resources/yard':{get:operation('120 wagons, four tracks, two shunters, yard baseline/results')},
 '/api/extension/resources/yard/optimize':{post:operation('Calculate destination grouping and track/shunter reservations')},
 '/api/extension/resources/yard/apply':{post:operation('Apply resource plan without altering traffic graph')},
 '/api/extension/simulation/{command}':{post:{...operation('Control extension simulation only'),parameters:[{name:'command',in:'path',required:true,schema:{enum:['pause','resume','reset','1','2','5']}}]}}
};
