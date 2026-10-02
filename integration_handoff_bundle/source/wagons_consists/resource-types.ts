

export interface Wagon {id:string;destination:string;cargo:string;priority:number;length_m:number;mass_t:number;arrival_time:number;deadline:number}

export interface YardTrain {id:string;destination:string;wagon_ids:string[];length_m:number;mass_t:number;length_limit_m:number;track_id:string;shunter_id:string;formation_start:number;formation_end:number;departure:number}

export interface YardData {station_id:string;reference_time:number;wagons:Wagon[];tracks:{id:string;length_m:number;max_mass_t:number;available_time:number}[];shunters:{id:string;available_time:number}[];max_train_length_m:number;max_train_mass_t:number}

export interface YardMetrics {train_count:number;wagon_hours:number;late_wagon_minutes:number;wagon_count:number;mean_fill_percent:number}

export interface OptimizationResult<P,M> {plan_id:string;version:number;before:P[];after:P[];before_metrics:M;after_metrics:M;objective_before:number;objective_after:number;calculation_time_ms:number;engine:string;constraints_verified:boolean;objective_formula:string;proof:Record<string,number>;slots_freed?:number;wagon_hours_saved?:number}

export interface ResourceState<D,P,M,R> {module:string;seed:number;provenance:string;data:D;baseline:P[];baseline_metrics:M;result:R|null;applied:{plan_id:string;option_id:string|null;time:number}|null;version:number}

export type YardState=ResourceState<YardData,YardTrain,YardMetrics,OptimizationResult<YardTrain,YardMetrics>>;
