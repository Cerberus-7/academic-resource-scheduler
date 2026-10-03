import { Fragment } from 'react'
import { Box, Paper, Typography, Tooltip } from '@mui/material'
import { DAYS, SLOT_LABELS, TimetableAllocationOut } from '../types'

const COLORS = ['#1565C0', '#2E7D32', '#B98900', '#6A1B9A', '#00838F', '#AD1457', '#37474F', '#5D4037']

function colorFor(key: number) {
  return COLORS[key % COLORS.length]
}

export default function TimetableGrid({ allocations, labelField = 'course' }: {
  allocations: TimetableAllocationOut[]
  labelField?: 'course' | 'resource' | 'faculty'
}) {
  const grid: Record<string, TimetableAllocationOut[]> = {}
  for (const a of allocations) {
    for (let offset = 0; offset < a.duration_hours; offset++) {
      const key = `${a.day_of_week}-${a.start_slot_index + offset}`
      grid[key] = grid[key] || []
      if (offset === 0) grid[key].push(a)
    }
  }

  return (
    <Paper variant="outlined" sx={{ overflowX: 'auto', p: 1 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: `90px repeat(${DAYS.length}, 1fr)`, minWidth: 900 }}>
        <Box />
        {DAYS.map((d) => (
          <Box key={d} sx={{ p: 1, fontWeight: 700, textAlign: 'center', borderBottom: '2px solid', borderColor: 'divider' }}>
            {d}
          </Box>
        ))}
        {SLOT_LABELS.map((label, slotIdx) => (
          <Fragment key={`row-${slotIdx}`}>
            <Box sx={{ p: 1, fontSize: 12, color: 'text.secondary', borderTop: '1px solid', borderColor: 'divider' }}>
              {label}
            </Box>
            {DAYS.map((_, dayIdx) => {
              const key = `${dayIdx}-${slotIdx}`
              const cellAllocs = grid[key] || []
              return (
                <Box key={key} sx={{ minHeight: 56, p: 0.5, borderTop: '1px solid', borderLeft: '1px solid', borderColor: 'divider' }}>
                  {cellAllocs.map((a) => {
                    const label = labelField === 'resource' ? a.resource_code : labelField === 'faculty' ? a.faculty_name : `${a.course_code}`
                    const sub = labelField === 'resource' ? a.course_code : labelField === 'faculty' ? a.course_code : a.resource_code
                    return (
                      <Tooltip
                        key={a.id}
                        title={`${a.course_name} · ${a.section_name} · ${a.faculty_name} · ${a.resource_name} (${a.status})`}
                      >
                        <Box sx={{
                          bgcolor: colorFor(a.id), color: '#fff', borderRadius: 1, p: 0.5, mb: 0.5,
                          fontSize: 11, lineHeight: 1.3, cursor: 'default',
                        }}>
                          <Typography variant="caption" sx={{ display: 'block', fontWeight: 700 }}>{label}</Typography>
                          <Typography variant="caption" sx={{ display: 'block', opacity: 0.85 }}>{sub}</Typography>
                        </Box>
                      </Tooltip>
                    )
                  })}
                </Box>
              )
            })}
          </Fragment>
        ))}
      </Box>
    </Paper>
  )
}
