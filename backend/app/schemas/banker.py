from typing import Optional
from pydantic import BaseModel

RESOURCE_TYPES = [
    "lecture_room_units",
    "computer_lab_units",
    "faculty_slot_units",
    "projector_units",
    "special_equipment_units",
]


class BankerInitRequest(BaseModel):
    total_resources: list[int]  # length == len(RESOURCE_TYPES)
    processes: dict[str, list[int]]  # process_name -> max_demand vector
    allocation: dict[str, list[int]] = {}  # process_name -> currently allocated vector


class BankerStateOut(BaseModel):
    resource_types: list[str]
    total: list[int]
    available: list[int]
    max_matrix: dict[str, list[int]]
    allocation_matrix: dict[str, list[int]]
    need_matrix: dict[str, list[int]]
    is_safe: bool
    safe_sequence: list[str]
    message: str = ""


class BankerRequestOp(BaseModel):
    process_name: str
    request_vector: list[int]


class BankerReleaseOp(BaseModel):
    process_name: str
    release_vector: list[int]


class BankerAddProcess(BaseModel):
    process_name: str
    max_demand: list[int]


class BankerAddResource(BaseModel):
    resource_index: int
    additional_units: int


class BankerReduceCapacity(BaseModel):
    resource_index: int
    reduced_units: int
    reason: str = "maintenance simulation"


class AuditLogOut(BaseModel):
    id: int
    actor_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: str
    is_override: bool
    created_at: str

    class Config:
        from_attributes = True
