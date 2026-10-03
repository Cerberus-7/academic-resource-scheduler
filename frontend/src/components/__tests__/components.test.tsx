import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusChip from '../StatusChip'
import KpiCard from '../KpiCard'
import TimetableGrid from '../TimetableGrid'
import { TimetableAllocationOut } from '../../types'

const alloc = (over: Partial<TimetableAllocationOut> = {}): TimetableAllocationOut => ({
  id: 1, course_session_id: 1, resource_id: 1, resource_name: 'Room 101', resource_code: 'R101',
  faculty_id: 1, faculty_name: 'Dr. Verma', section_id: 1, section_name: 'CSE-3A',
  course_code: 'CS301', course_name: 'Operating Systems', day_of_week: 0, start_slot_index: 0,
  duration_hours: 1, status: 'active', version: 1, ...over,
})

describe('StatusChip', () => {
  it('renders status text with underscores replaced', () => {
    render(<StatusChip status="under_discussion" />)
    expect(screen.getByText('under discussion')).toBeInTheDocument()
  })
  it('uses success colour for approved and error colour for rejected', () => {
    const { container: a } = render(<StatusChip status="approved" />)
    const { container: b } = render(<StatusChip status="rejected" />)
    expect(a.querySelector('.MuiChip-colorSuccess')).not.toBeNull()
    expect(b.querySelector('.MuiChip-colorError')).not.toBeNull()
  })
})

describe('KpiCard', () => {
  it('shows title and value', () => {
    render(<KpiCard title="Pending Requests" value={7} icon={<span>i</span>} />)
    expect(screen.getByText('Pending Requests')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
  })
})

describe('TimetableGrid', () => {
  it('renders day headers and an allocation label', () => {
    render(<TimetableGrid allocations={[alloc()]} />)
    expect(screen.getByText('Monday')).toBeInTheDocument()
    expect(screen.getByText('Saturday')).toBeInTheDocument()
    expect(screen.getByText('CS301')).toBeInTheDocument()
  })
  it('renders a multi-hour session only once (in its first slot)', () => {
    render(<TimetableGrid allocations={[alloc({ duration_hours: 2 })]} />)
    expect(screen.getAllByText('CS301')).toHaveLength(1)
  })
  it('can label by room instead of course', () => {
    render(<TimetableGrid allocations={[alloc()]} labelField="resource" />)
    expect(screen.getAllByText('R101').length).toBeGreaterThan(0)
  })
})
