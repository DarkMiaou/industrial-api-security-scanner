from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status

from .audit import AuditStore
from .config import Settings
from .models import (
    Identity,
    MaintenanceOrder,
    Pump,
    SetpointRequest,
    StationSnapshot,
    StationStore,
    Telemetry,
    TokenRequest,
    TokenResponse,
)
from .rate_limit import FixedWindowRateLimiter
from .security import (
    authenticate,
    create_token,
    optional_identity,
    require_identity,
    require_role,
)

ORDERS = [
    MaintenanceOrder(
        id=100,
        pump_id="pump-001",
        description="Inspect inlet valve",
        status="open",
    ),
    MaintenanceOrder(
        id=101,
        pump_id="pump-002",
        description="Check bearing temperature",
        status="scheduled",
    ),
]


def _correlation_id(value: str | None) -> str:
    return value or str(uuid4())


def _command_allowed(request: Request, identity: Identity | None) -> Identity:
    if request.app.state.settings.profile == "vulnerable":
        return identity or Identity(username="anonymous", role="guest")
    if identity is None:
        raise HTTPException(status_code=401, detail="Gateway authentication required")
    require_role(identity, "supervisor", "admin")
    return identity


def _apply_command_limit(request: Request, identity: Identity) -> None:
    settings: Settings = request.app.state.settings
    if settings.profile != "hardened":
        return
    allowed, retry_after = request.app.state.rate_limiter.check(
        f"command:{identity.username}",
        limit=settings.command_limit,
        window_seconds=settings.rate_window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OT command rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings.from_env()
    gateway = FastAPI(
        title="IASS OT Gateway Demo",
        version="0.1.0",
        description="Local simulation only. It never controls industrial equipment.",
    )
    gateway.state.settings = active_settings
    gateway.state.station = StationStore()
    gateway.state.audit = AuditStore()
    gateway.state.rate_limiter = FixedWindowRateLimiter()

    @gateway.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "profile": active_settings.profile}

    @gateway.post("/auth/token", response_model=TokenResponse)
    def issue_token(payload: TokenRequest, request: Request) -> TokenResponse:
        identity = authenticate(payload.username, payload.password)
        if identity is None:
            if active_settings.profile == "hardened":
                client = request.client.host if request.client else "unknown"
                allowed, retry_after = request.app.state.rate_limiter.check(
                    f"auth:{client}",
                    limit=active_settings.auth_limit,
                    window_seconds=active_settings.rate_window_seconds,
                )
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail="Authentication rate limit exceeded",
                        headers={"Retry-After": str(retry_after)},
                    )
            raise HTTPException(status_code=401, detail="Invalid gateway credentials")
        token = create_token(identity, active_settings)
        return TokenResponse(
            access_token=token,
            role=identity.role,
            zone=identity.zone,
        )

    @gateway.get("/telemetry", response_model=Telemetry)
    def telemetry(
        identity: Annotated[Identity | None, Depends(optional_identity)],
    ) -> Telemetry:
        if active_settings.profile == "hardened":
            if identity is None:
                raise HTTPException(status_code=401, detail="Gateway authentication required")
            require_role(identity, "operator", "supervisor", "admin")
        return gateway.state.station.telemetry()

    @gateway.get("/pumps/{pump_id}", response_model=Pump)
    def get_pump(
        pump_id: str,
        identity: Annotated[Identity, Depends(require_identity)],
    ) -> Pump:
        pump = gateway.state.station.pump(pump_id)
        if pump is None:
            raise HTTPException(status_code=404, detail="Pump not found")
        if active_settings.profile == "hardened":
            require_role(identity, "operator", "supervisor", "admin")
            if identity.role == "operator" and identity.zone != pump.zone:
                raise HTTPException(status_code=403, detail="Pump belongs to another zone")
        return pump

    def change_pump_status(
        pump_id: str,
        desired_status: Literal["running", "stopped"],
        request: Request,
        identity: Identity | None,
        correlation_header: str | None,
    ) -> Pump:
        pump = gateway.state.station.pump(pump_id)
        if pump is None:
            raise HTTPException(status_code=404, detail="Pump not found")
        actor = _command_allowed(request, identity)
        _apply_command_limit(request, actor)
        updated = gateway.state.station.set_pump_status(pump_id, desired_status)
        if updated is None:
            raise HTTPException(status_code=404, detail="Pump not found")
        if active_settings.profile == "hardened":
            gateway.state.audit.record(
                actor=actor.username,
                action=f"pump.{ 'start' if desired_status == 'running' else 'stop' }",
                resource=pump_id,
                result="allowed",
                correlation_id=_correlation_id(correlation_header),
            )
        return updated

    @gateway.post("/pumps/{pump_id}/start", response_model=Pump)
    def start_pump(
        pump_id: str,
        request: Request,
        identity: Annotated[Identity | None, Depends(optional_identity)],
        x_correlation_id: Annotated[str | None, Header()] = None,
    ) -> Pump:
        return change_pump_status(
            pump_id, "running", request, identity, x_correlation_id
        )

    @gateway.post("/pumps/{pump_id}/stop", response_model=Pump)
    def stop_pump(
        pump_id: str,
        request: Request,
        identity: Annotated[Identity | None, Depends(optional_identity)],
        x_correlation_id: Annotated[str | None, Header()] = None,
    ) -> Pump:
        return change_pump_status(
            pump_id, "stopped", request, identity, x_correlation_id
        )

    @gateway.put("/process/setpoint", response_model=Telemetry)
    def set_setpoint(
        payload: SetpointRequest,
        request: Request,
        identity: Annotated[Identity | None, Depends(optional_identity)],
        x_correlation_id: Annotated[str | None, Header()] = None,
    ) -> Telemetry:
        actor = _command_allowed(request, identity)
        _apply_command_limit(request, actor)
        result = gateway.state.station.set_setpoint(payload.pressure_bar)
        if active_settings.profile == "hardened":
            gateway.state.audit.record(
                actor=actor.username,
                action="process.setpoint",
                resource="water-process",
                result="allowed",
                correlation_id=_correlation_id(x_correlation_id),
            )
        return result

    @gateway.post("/process/emergency-stop", response_model=Telemetry)
    def emergency_stop(
        request: Request,
        identity: Annotated[Identity | None, Depends(optional_identity)],
        x_confirm_emergency_stop: Annotated[str | None, Header()] = None,
        x_correlation_id: Annotated[str | None, Header()] = None,
    ) -> Telemetry:
        if active_settings.profile == "hardened":
            if identity is None:
                raise HTTPException(status_code=401, detail="Gateway authentication required")
            require_role(identity, "admin")
            if x_confirm_emergency_stop != "true":
                raise HTTPException(status_code=403, detail="Explicit confirmation required")
        actor = identity or Identity(username="anonymous", role="guest")
        _apply_command_limit(request, actor)
        result = gateway.state.station.set_emergency_stop()
        if active_settings.profile == "hardened":
            gateway.state.audit.record(
                actor=actor.username,
                action="process.emergency_stop",
                resource="water-process",
                result="allowed",
                correlation_id=_correlation_id(x_correlation_id),
            )
        return result

    @gateway.get("/audit/events")
    def audit_events(
        identity: Annotated[Identity, Depends(require_identity)],
        correlation_id: Annotated[str | None, Query(max_length=128)] = None,
    ) -> dict[str, object]:
        if active_settings.profile == "hardened":
            require_role(identity, "admin")
            events = gateway.state.audit.find(correlation_id)
            return {"events": [event.model_dump(mode="json") for event in events]}
        return {"events": []}

    @gateway.get("/maintenance/orders")
    def maintenance_orders(
        id: Annotated[str, Query(min_length=1, max_length=64)],
        identity: Annotated[Identity, Depends(require_identity)],
    ) -> dict[str, object]:
        if active_settings.profile == "hardened":
            require_role(identity, "operator", "supervisor", "admin")
            if not id.isdigit():
                raise HTTPException(status_code=422, detail="Order id must be an integer")
            matches = [order for order in ORDERS if order.id == int(id)]
        else:
            normalized = id.lower().replace(" ", "")
            if "'" in id:
                raise HTTPException(
                    status_code=500,
                    detail="SQL syntax error near unexpected quote",
                )
            if "or1=1" in normalized or "or'1'='1" in normalized:
                matches = ORDERS
            elif "or1=2" in normalized or "or'1'='2" in normalized:
                matches = []
            elif id.isdigit():
                matches = [order for order in ORDERS if order.id == int(id)]
            else:
                matches = []
        return {"orders": [order.model_dump() for order in matches]}

    @gateway.post("/demo/reset", response_model=StationSnapshot)
    def reset_demo(
        x_demo_key: Annotated[str | None, Header()] = None,
    ) -> StationSnapshot:
        if x_demo_key != active_settings.demo_reset_key:
            raise HTTPException(status_code=403, detail="Invalid demonstration reset key")
        snapshot = gateway.state.station.reset()
        gateway.state.audit.clear()
        gateway.state.rate_limiter.clear()
        return snapshot

    return gateway


app = create_app()
