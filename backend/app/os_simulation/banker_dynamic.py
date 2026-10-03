"""
Dynamic Banker-style extension on top of the classical algorithm:
- add a process/request at runtime
- add resource capacity at runtime
- reduce free capacity at runtime (maintenance simulation)
- re-run the safety check after EVERY state mutation
- reject any mutation that would leave the system in an unsafe state

Still purely an abstract OS-education simulation; never touches the real
timetable tables.
"""
from app.os_simulation.banker_classic import BankerState, is_safe_state


def add_process(state: BankerState, process_name: str, max_demand: list[int]) -> tuple[bool, str, BankerState]:
    if process_name in state.max_matrix:
        return False, f"Process '{process_name}' already exists.", state
    if any(m > t for m, t in zip(max_demand, state.total)):
        return False, "Max demand for a resource type cannot exceed total system capacity.", state
    new_max = dict(state.max_matrix)
    new_max[process_name] = max_demand
    new_alloc = dict(state.allocation_matrix)
    new_alloc[process_name] = [0] * state.n_resources
    new_state = BankerState(state.resource_types, state.total, new_max, new_alloc)
    safe, seq = is_safe_state(new_state)
    if not safe:
        return False, "Adding this process would make the system unsafe. Rejected.", state
    return True, f"Process '{process_name}' added. Safe sequence: {seq}", new_state


def add_resource_capacity(state: BankerState, resource_index: int, additional_units: int) -> tuple[bool, str, BankerState]:
    if not (0 <= resource_index < state.n_resources):
        return False, "Invalid resource index.", state
    new_total = state.total[:]
    new_total[resource_index] += additional_units
    new_state = BankerState(state.resource_types, new_total, state.max_matrix, state.allocation_matrix)
    safe, seq = is_safe_state(new_state)
    # Adding capacity can only help safety, but we re-check per the spec anyway.
    if not safe:
        return False, "Unexpected: system remains unsafe even after adding capacity.", state
    return True, f"Added {additional_units} units to {state.resource_types[resource_index]}.", new_state


def reduce_resource_capacity(
    state: BankerState, resource_index: int, reduced_units: int, reason: str = "maintenance simulation"
) -> tuple[bool, str, BankerState]:
    if not (0 <= resource_index < state.n_resources):
        return False, "Invalid resource index.", state
    available = state.available()
    if reduced_units > available[resource_index]:
        return False, (
            f"Cannot take {reduced_units} units of {state.resource_types[resource_index]} offline — "
            f"only {available[resource_index]} currently free (rest are allocated)."
        ), state
    new_total = state.total[:]
    new_total[resource_index] -= reduced_units
    new_state = BankerState(state.resource_types, new_total, state.max_matrix, state.allocation_matrix)
    safe, seq = is_safe_state(new_state)
    if not safe:
        return False, f"Reducing {state.resource_types[resource_index]} by {reduced_units} would make the system unsafe. Rejected.", state
    return True, f"Reduced {state.resource_types[resource_index]} by {reduced_units} units ({reason}). Safe sequence: {seq}", new_state
