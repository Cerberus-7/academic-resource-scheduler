"""
Classical Banker's Algorithm over ABSTRACT resource-unit types:
    lecture_room_units, computer_lab_units, faculty_slot_units,
    projector_units, special_equipment_units

This is a standalone Operating-Systems safety-simulation module. It is
NEVER used to approve final room/time/faculty allocations — that decision is
made exclusively by CP-SAT (see app/solver/cp_sat_scheduler.py).
"""
from dataclasses import dataclass, field


@dataclass
class BankerState:
    resource_types: list[str]
    total: list[int]
    max_matrix: dict[str, list[int]] = field(default_factory=dict)
    allocation_matrix: dict[str, list[int]] = field(default_factory=dict)

    @property
    def n_resources(self) -> int:
        return len(self.resource_types)

    def allocated_total(self) -> list[int]:
        totals = [0] * self.n_resources
        for vec in self.allocation_matrix.values():
            for i, v in enumerate(vec):
                totals[i] += v
        return totals

    def available(self) -> list[int]:
        allocated = self.allocated_total()
        return [self.total[i] - allocated[i] for i in range(self.n_resources)]

    def need_matrix(self) -> dict[str, list[int]]:
        need = {}
        for p, max_vec in self.max_matrix.items():
            alloc_vec = self.allocation_matrix.get(p, [0] * self.n_resources)
            need[p] = [max_vec[i] - alloc_vec[i] for i in range(self.n_resources)]
        return need


def is_safe_state(state: BankerState) -> tuple[bool, list[str]]:
    work = state.available()[:]
    need = state.need_matrix()
    finished = {p: False for p in state.max_matrix}
    safe_sequence: list[str] = []

    changed = True
    while changed:
        changed = False
        for p in state.max_matrix:
            if finished[p]:
                continue
            need_vec = need[p]
            if all(need_vec[i] <= work[i] for i in range(state.n_resources)):
                for i in range(state.n_resources):
                    work[i] += state.allocation_matrix.get(p, [0] * state.n_resources)[i]
                finished[p] = True
                safe_sequence.append(p)
                changed = True
    is_safe = all(finished.values())
    return is_safe, safe_sequence


def request_resources(state: BankerState, process: str, request_vec: list[int]) -> tuple[bool, str, BankerState]:
    if process not in state.max_matrix:
        return False, f"Unknown process '{process}'.", state
    need = state.need_matrix()[process]
    if any(request_vec[i] > need[i] for i in range(state.n_resources)):
        return False, "Request exceeds declared maximum need for this process.", state
    available = state.available()
    if any(request_vec[i] > available[i] for i in range(state.n_resources)):
        return False, "Request exceeds currently available resources — process must wait.", state

    # Tentatively allocate
    trial_alloc = dict(state.allocation_matrix)
    current = trial_alloc.get(process, [0] * state.n_resources)
    trial_alloc[process] = [current[i] + request_vec[i] for i in range(state.n_resources)]
    trial_state = BankerState(state.resource_types, state.total, state.max_matrix, trial_alloc)

    safe, _ = is_safe_state(trial_state)
    if not safe:
        return False, "Granting this request would lead to an unsafe state. Request rejected/deferred.", state
    return True, "Request granted — resulting state is safe.", trial_state


def release_resources(state: BankerState, process: str, release_vec: list[int]) -> tuple[bool, str, BankerState]:
    if process not in state.allocation_matrix:
        return False, f"Process '{process}' currently holds no resources.", state
    current = state.allocation_matrix[process]
    if any(release_vec[i] > current[i] for i in range(state.n_resources)):
        return False, "Cannot release more than currently allocated.", state
    new_alloc = dict(state.allocation_matrix)
    new_alloc[process] = [current[i] - release_vec[i] for i in range(state.n_resources)]
    new_state = BankerState(state.resource_types, state.total, state.max_matrix, new_alloc)
    return True, "Resources released.", new_state
