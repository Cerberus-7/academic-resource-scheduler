export type RoleName = 'admin' | 'professor' | 'event_coordinator' | 'student'

export interface UserOut {
  id: number
  full_name: string
  email: string
  role: RoleName
  is_active: boolean
}

export interface ResourceOut {
  id: number
  name: string
  code: string
  resource_type: 'room' | 'lab'
  building: string
  floor: string
  capacity: number
  is_active: boolean
  notes: string
  facilities: { id: number; name: string }[]
}

export interface FacultyOut {
  id: number
  employee_code: string
  full_name: string
  department: string
  designation: string
  user_id: number | null
}

export interface CourseOut {
  id: number
  code: string
  name: string
  credits: number
  requires_lab: boolean
}

export interface StudentSectionOut {
  id: number
  name: string
  course_id: number
  student_count: number
  semester: number
}

export interface CourseSessionOut {
  id: number
  section_id: number
  faculty_id: number
  session_type: string
  duration_hours: number
  sessions_per_week: number
  required_resource_type: string
  required_facility_names: string
}

export interface TimetableAllocationOut {
  id: number
  course_session_id: number | null
  resource_id: number
  resource_name: string
  resource_code: string
  faculty_id: number | null
  faculty_name: string
  section_id: number | null
  section_name: string
  course_code: string
  course_name: string
  day_of_week: number
  start_slot_index: number
  duration_hours: number
  status: string
  version: number
}

export interface AvailabilityResult {
  resource_id: number
  name: string
  code: string
  resource_type: string
  capacity: number
  building: string
  facilities: string[]
  is_suitable: boolean
  available_from: string
  available_until: string
  max_continuous_hours: number
  next_booking: string | null
  status: string
}

export interface ScheduleRequestOut {
  id: number
  request_type: string
  requested_by_id: number
  title: string
  reason: string
  duration_hours: number
  required_resource_type: string
  base_priority: number
  arrival_time: string
  status: string
  failure_reason: string
  assigned_allocation_id: number | null
  effective_priority?: number | null
  waiting_seconds?: number | null
}

export interface ShiftAlternativeOut {
  id: number
  shift_request_id: number
  resource_id: number
  day_of_week: number
  start_slot_index: number
  duration_hours: number
  is_cp_sat_valid: boolean
  validation_message: string
  is_selected: boolean
}

export interface ShiftRequestOut {
  id: number
  original_allocation_id: number
  affected_faculty_id: number
  requested_by_id: number
  reason_code: string
  reason_text: string
  base_priority: number
  arrival_time: string
  decision_deadline: string | null
  status: string
  final_decision: string
  alternatives: ShiftAlternativeOut[]
}

export interface DiscussionMessageOut {
  id: number
  shift_request_id: number
  sender_id: number
  sender_name: string | null
  message: string
  created_at: string
}

export const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
export const SLOT_LABELS = Array.from({ length: 8 }, (_, i) => `${9 + i}:00`)
