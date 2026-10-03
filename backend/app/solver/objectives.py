"""Objective helpers.

For full timetable generation we simply look for any feasible solution
(satisfying all hard constraints) since a college timetable rarely needs a
secondary optimization objective beyond feasibility; if desired this can be
extended with soft preferences.

For dynamic rescheduling we minimize a weighted disruption score:
    changed_room * 2 + changed_day * 3 + changed_start_time * 1
    + changed_faculty * 5 + (num_sessions_moved) * 10
This is computed in Python (not inside CP-SAT) because we generate a small
set of CP-SAT-validated candidate alternatives per affected session and then
pick the minimum-disruption candidate — this keeps the solver invocation
simple (feasibility-only per candidate) while still making CP-SAT the final
authority on whether a candidate is legal.
"""


def disruption_score(
    original_resource_id: int, new_resource_id: int,
    original_day: int, new_day: int,
    original_start_slot: int, new_start_slot: int,
    original_faculty_id: int, new_faculty_id: int,
) -> int:
    score = 0
    if original_resource_id != new_resource_id:
        score += 2
    if original_day != new_day:
        score += 3
    if original_start_slot != new_start_slot:
        score += 1
    if original_faculty_id != new_faculty_id:
        score += 5
    return score
