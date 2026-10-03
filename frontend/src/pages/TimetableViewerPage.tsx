import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Paper, Grid, MenuItem, TextField, ToggleButtonGroup, ToggleButton } from '@mui/material'
import { api } from '../api/client'
import { DAYS, TimetableAllocationOut } from '../types'
import TimetableGrid from '../components/TimetableGrid'

export default function TimetableViewerPage({ title, defaultFacultyId, defaultSectionId, readOnlyFilters }: {
  title: string
  defaultFacultyId?: number
  defaultSectionId?: number
  readOnlyFilters?: boolean
}) {
  const [sectionId, setSectionId] = useState<number | ''>(defaultSectionId ?? '')
  const [facultyId, setFacultyId] = useState<number | ''>(defaultFacultyId ?? '')
  const [resourceId, setResourceId] = useState<number | ''>('')
  const [dayOfWeek, setDayOfWeek] = useState<number | ''>('')
  const [labelField, setLabelField] = useState<'course' | 'resource' | 'faculty'>('course')

  const { data: sections } = useQuery({ queryKey: ['sections'], queryFn: () => api.get('/courses/sections').then(r => r.data), enabled: !readOnlyFilters || true })
  const { data: faculty } = useQuery({ queryKey: ['faculty'], queryFn: () => api.get('/faculty').then(r => r.data) })
  const { data: resources } = useQuery({ queryKey: ['resources'], queryFn: () => api.get('/resources').then(r => r.data) })

  const { data: allocations = [], isLoading } = useQuery<TimetableAllocationOut[]>({
    queryKey: ['timetable', sectionId, facultyId, resourceId, dayOfWeek],
    queryFn: () => api.get('/timetable', {
      params: {
        section_id: sectionId || undefined, faculty_id: facultyId || undefined,
        resource_id: resourceId || undefined, day_of_week: dayOfWeek === '' ? undefined : dayOfWeek,
      },
    }).then(r => r.data),
  })

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>{title}</Typography>
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField select fullWidth size="small" label="Section" value={sectionId} onChange={(e) => setSectionId(e.target.value ? Number(e.target.value) : '')}>
              <MenuItem value="">All sections</MenuItem>
              {sections?.map((s: any) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField select fullWidth size="small" label="Faculty" value={facultyId} onChange={(e) => setFacultyId(e.target.value ? Number(e.target.value) : '')}>
              <MenuItem value="">All faculty</MenuItem>
              {faculty?.map((f: any) => <MenuItem key={f.id} value={f.id}>{f.full_name}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField select fullWidth size="small" label="Room / Lab" value={resourceId} onChange={(e) => setResourceId(e.target.value ? Number(e.target.value) : '')}>
              <MenuItem value="">All rooms/labs</MenuItem>
              {resources?.map((r: any) => <MenuItem key={r.id} value={r.id}>{r.name} ({r.code})</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField select fullWidth size="small" label="Day" value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value === '' ? '' : Number(e.target.value))}>
              <MenuItem value="">All days</MenuItem>
              {DAYS.map((d, i) => <MenuItem key={d} value={i}>{d}</MenuItem>)}
            </TextField>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2 }}>
          <ToggleButtonGroup size="small" exclusive value={labelField} onChange={(_, v) => v && setLabelField(v)}>
            <ToggleButton value="course">Show course</ToggleButton>
            <ToggleButton value="resource">Show room/lab</ToggleButton>
            <ToggleButton value="faculty">Show faculty</ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Paper>
      {!isLoading && allocations.length === 0 && (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">No timetable entries match these filters yet.</Typography>
        </Paper>
      )}
      {allocations.length > 0 && <TimetableGrid allocations={allocations} labelField={labelField} />}
    </Box>
  )
}
