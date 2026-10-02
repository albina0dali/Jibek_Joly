from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Station(BaseModel):
    id: str
    name: str
    distance_km: float
    platform_count: int
    siding_available: bool


class Block(BaseModel):
    id: str
    from_station: str
    to_station: str
    start_km: float
    end_km: float
    distance_km: float
    track_type: str
    directionality: str = 'bidirectional'
    speed_limit_kmh: int
    capacity: int
    status: str = 'free'


class Train(BaseModel):
    id: str
    service_number: str
    type: str
    priority: int
    origin: str
    destination: str
    length_m: int
    max_speed_kmh: int
    scheduled_departure: int
    scheduled_arrival: int = 0
    planned_stops: list[str]
    direction: int


class Visit(BaseModel):
    train_id: str
    resource: str
    kind: Literal['block', 'station']
    start: int
    end: int
    from_km: float
    to_km: float
    direction: int
    lane: int = 0


class IncidentInput(BaseModel):
    type: Literal['delay_5', 'delay_10', 'signal_failure', 'block_closure', 'speed_restriction', 'prolonged_dwell']
    location_id: str
    duration: int = Field(default=600, ge=60, le=1800)


class Settings(BaseModel):
    simulation_speed: Literal[1, 2, 5] = 1
    quality_weights: dict[str, float] = Field(default_factory=lambda: {'schedule': 30, 'capacity': 20, 'energy': 20, 'conflict': 20, 'arrival': 10})
    attention_threshold: float = Field(default=60, ge=0, le=99)
    normal_threshold: float = Field(default=80, ge=1, le=100)
    minimum_headway: int = Field(default=60, ge=15, le=180)
    max_optimizer_runtime: float = Field(default=2, ge=.1, le=3)
    objective_weights: dict[str, float] = Field(default_factory=lambda: {'delay': 1, 'priority': 3, 'stops': 1, 'deviation': 1})

    @model_validator(mode='after')
    def validate_configuration(self):
        if set(self.quality_weights) != {'schedule', 'capacity', 'energy', 'conflict', 'arrival'} or abs(sum(self.quality_weights.values()) - 100) > .001 or min(self.quality_weights.values()) < 0:
            raise ValueError('Quality weights must be nonnegative and sum to 100%')
        if self.attention_threshold >= self.normal_threshold:
            raise ValueError('Normal threshold must exceed attention threshold')
        if set(self.objective_weights) != {'delay', 'priority', 'stops', 'deviation'} or min(self.objective_weights.values()) < 0 or not any(self.objective_weights.values()):
            raise ValueError('Provide nonnegative objective weights with at least one positive value')
        return self
