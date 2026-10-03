from sqlalchemy.orm import Session
from app.os_simulation.banker_classic import BankerState, is_safe_state, request_resources, release_resources
from app.os_simulation import banker_dynamic
from app.models.logs import BankerSimulationState
from app.schemas.banker import RESOURCE_TYPES

# In-memory "live" state for the current demo session (also persisted as a
# log trail in banker_simulation_states for the audit/history view).
_current_state: BankerState | None = None


def _persist(db: Session, state: BankerState, event: str):
    is_safe, seq = is_safe_state(state)
    db.add(BankerSimulationState(
        snapshot_label=event, resource_types=state.resource_types, available=state.available(),
        max_matrix=state.max_matrix, allocation_matrix=state.allocation_matrix,
        is_safe=is_safe, safe_sequence=seq, event=event,
    ))
    db.commit()


def _state_to_dict(state: BankerState, message: str = "") -> dict:
    is_safe, seq = is_safe_state(state)
    return {
        "resource_types": state.resource_types, "total": state.total, "available": state.available(),
        "max_matrix": state.max_matrix, "allocation_matrix": state.allocation_matrix,
        "need_matrix": state.need_matrix(), "is_safe": is_safe, "safe_sequence": seq, "message": message,
    }


def init_state(db: Session, total_resources: list[int], processes: dict, allocation: dict) -> dict:
    global _current_state
    _current_state = BankerState(RESOURCE_TYPES, total_resources, processes, allocation or {
        p: [0] * len(RESOURCE_TYPES) for p in processes
    })
    _persist(db, _current_state, "init")
    return _state_to_dict(_current_state, "Banker state initialized.")


def get_state() -> dict:
    if _current_state is None:
        return _state_to_dict(BankerState(RESOURCE_TYPES, [0] * len(RESOURCE_TYPES), {}, {}))
    return _state_to_dict(_current_state)


def request(db: Session, process_name: str, request_vector: list[int]) -> dict:
    global _current_state
    if _current_state is None:
        raise ValueError("Banker state not initialized. Call init first.")
    ok, msg, new_state = request_resources(_current_state, process_name, request_vector)
    if ok:
        _current_state = new_state
        _persist(db, _current_state, f"request:{process_name}")
    return _state_to_dict(_current_state, msg)


def release(db: Session, process_name: str, release_vector: list[int]) -> dict:
    global _current_state
    if _current_state is None:
        raise ValueError("Banker state not initialized. Call init first.")
    ok, msg, new_state = release_resources(_current_state, process_name, release_vector)
    if ok:
        _current_state = new_state
        _persist(db, _current_state, f"release:{process_name}")
    return _state_to_dict(_current_state, msg)


def add_process(db: Session, process_name: str, max_demand: list[int]) -> dict:
    global _current_state
    if _current_state is None:
        raise ValueError("Banker state not initialized. Call init first.")
    ok, msg, new_state = banker_dynamic.add_process(_current_state, process_name, max_demand)
    if ok:
        _current_state = new_state
        _persist(db, _current_state, f"add_process:{process_name}")
    return _state_to_dict(_current_state, msg)


def add_resource_capacity(db: Session, resource_index: int, additional_units: int) -> dict:
    global _current_state
    if _current_state is None:
        raise ValueError("Banker state not initialized. Call init first.")
    ok, msg, new_state = banker_dynamic.add_resource_capacity(_current_state, resource_index, additional_units)
    if ok:
        _current_state = new_state
        _persist(db, _current_state, "add_resource_capacity")
    return _state_to_dict(_current_state, msg)


def reduce_resource_capacity(db: Session, resource_index: int, reduced_units: int, reason: str) -> dict:
    global _current_state
    if _current_state is None:
        raise ValueError("Banker state not initialized. Call init first.")
    ok, msg, new_state = banker_dynamic.reduce_resource_capacity(_current_state, resource_index, reduced_units, reason)
    if ok:
        _current_state = new_state
        _persist(db, _current_state, "reduce_resource_capacity")
    return _state_to_dict(_current_state, msg)


def history(db: Session, limit: int = 50) -> list[BankerSimulationState]:
    return db.query(BankerSimulationState).order_by(BankerSimulationState.id.desc()).limit(limit).all()
