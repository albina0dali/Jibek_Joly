

export interface Station {id:string;name:string;distance_km:number;platform_count:number;siding_available:boolean}

export interface Block {id:string;from_station:string;to_station:string;start_km:number;end_km:number;distance_km:number;track_type:string;speed_limit_kmh:number;status:string}

export interface Conflict {id:string;type:string;severity:string;location:string;start_time:number;affected_trains:string[];description:string;predicted_delay:number;status:string}

export interface Incident {id:string;type:string;location_id:string;start_time:number;end_time:number;expected_duration:number;status:string;severity:string}

export interface Train {id:string;train_id:string;type:string;service_number:string;priority:number;origin:string;destination:string;direction:number;length_m:number;max_speed_kmh:number;block_id:string|null;distance_km:number;speed_kmh:number;allowed_speed:number;delay_seconds:number;status:string;next_station:string;eta:number;next_station_eta:number;recommendation:string;energy_estimate:number;upcoming_conflicts:Conflict[]}

export interface Visit {train_id:string;resource:string;kind:string;start:number;end:number;from_km:number;to_km:number;direction:number}

export interface Quality {value:number;category:string;formula:string;components:{name:string;score:number;weight:number;contribution:number;reason:string}[];factors:{label:string;impact:number}[]}

export interface Option {id:string;label:string;objective:string;actions:string[];explanation:string;estimated_total_delay:number;affected_train_count:number;remaining_conflicts:number;quality_index:number;calculation_time_ms:number;engine:string;recovery_time:number;schedule:Visit[]}

export interface Snapshot {time:number;paused:boolean;speed:number;trains:Train[];stations:Station[];blocks:Block[];signals:{id:string;block_id:string;direction:number;status:string}[];conflicts:Conflict[];incidents:Incident[];quality:Quality;schedule:Visit[];baseline:Visit[];options:Option[];selected_recommendation:string|null;replanning:boolean;optimizer_error:string|null;revision:number}

export interface Session {token:string;username:string;role:string}
