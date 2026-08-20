from datetime import datetime
from threading import RLock
from typing import Literal

from pydantic import BaseModel, Field

PumpStatus = Literal["running", "stopped"]
Role = Literal["guest", "operator", "supervisor", "admin"]


class Pump(BaseModel):
    id: str
    zone: Literal["A", "B"]
    status: PumpStatus


class Telemetry(BaseModel):
    pressure_bar: float
    flow_l_min: int
    level_percent: int
    emergency_stop: bool
    setpoint_bar: float


class StationSnapshot(BaseModel):
    pumps: list[Pump]
    telemetry: Telemetry


class StationStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> StationSnapshot:
        with self._lock:
            self._pumps = {
                "pump-001": Pump(id="pump-001", zone="A", status="stopped"),
                "pump-002": Pump(id="pump-002", zone="B", status="running"),
            }
            self._telemetry = Telemetry(
                pressure_bar=2.5,
                flow_l_min=120,
                level_percent=65,
                emergency_stop=False,
                setpoint_bar=2.5,
            )
            return self.snapshot()

    def snapshot(self) -> StationSnapshot:
        with self._lock:
            return StationSnapshot(
                pumps=[pump.model_copy() for pump in self._pumps.values()],
                telemetry=self._telemetry.model_copy(),
            )

    def telemetry(self) -> Telemetry:
        with self._lock:
            return self._telemetry.model_copy()

    def pump(self, pump_id: str) -> Pump | None:
        with self._lock:
            pump = self._pumps.get(pump_id)
            return pump.model_copy() if pump else None

    def set_pump_status(self, pump_id: str, status: PumpStatus) -> Pump | None:
        with self._lock:
            pump = self._pumps.get(pump_id)
            if pump is None:
                return None
            pump.status = status
            return pump.model_copy()

    def set_setpoint(self, value: float) -> Telemetry:
        with self._lock:
            self._telemetry.setpoint_bar = value
            return self._telemetry.model_copy()

    def set_emergency_stop(self) -> Telemetry:
        with self._lock:
            self._telemetry.emergency_stop = True
            for pump in self._pumps.values():
                pump.status = "stopped"
            return self._telemetry.model_copy()


class TokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: Role
    zone: Literal["A", "B"] | None


class Identity(BaseModel):
    username: str
    role: Role
    zone: Literal["A", "B"] | None = None


class SetpointRequest(BaseModel):
    pressure_bar: float = Field(ge=1.0, le=5.0)


class AuditEvent(BaseModel):
    actor: str
    action: str
    resource: str
    result: Literal["allowed", "denied"]
    timestamp: datetime
    correlation_id: str


class MaintenanceOrder(BaseModel):
    id: int
    pump_id: str
    description: str
    status: Literal["open", "scheduled", "closed"]

