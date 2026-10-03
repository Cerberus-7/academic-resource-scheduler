import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Box, Typography, Paper, Grid, TextField, MenuItem, Button, Stack, Alert } from '@mui/material'
import { api, getErrorMessage } from '../api/client'
import { DAYS, SLOT_LABELS } from '../types'
import { useAuth } from '../hooks/useAuth'

export default function ScheduleRequestFormPage({ title, requestTypes, defaultFacultyId }: {
  title: string
  requestTypes: { value: string; label: string }[]
  defaultFacultyId?: number
}) {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const { data: sections = [] } = useQuery({ queryKey: ['sections'], queryFn: () => api.get('/courses/sections').then(r => r.data) })
  const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: () => api.get('/courses').then(r => r.data) })
  const { data: faculty = [] } = useQuery({ queryKey: ['faculty'], queryFn: () => api.get('/faculty').then(r => r.data) })

  const [form, setForm] = useState({
    request_type: requestTypes[0]?.value ?? '', title: '', reason: '', course_id: '', section_id: '',
    faculty_id: defaultFacultyId ?? '', student_count: 30, duration_hours: 1, required_resource_type: 'room',
    required_facility_names: '', preferred_day_of_week: '', preferred_start_slot_index: '', base_priority: 5,
  })

  const create = useMutation({
    mutationFn: () => api.post('/schedule-requests', {
      ...form,
      course_id: form.course_id || undefined,
      section_id: form.section_id || undefined,
      faculty_id: form.faculty_id || undefined,
      preferred_day_of_week: form.preferred_day_of_week === '' ? undefined : Number(form.preferred_day_of_week),
      preferred_start_slot_index: form.preferred_start_slot_index === '' ? undefined : Number(form.preferred_start_slot_index),
    }),
    onSuccess: () => {
      setSuccess('Request submitted successfully. It has been added to the priority queue.')
      setError('')
      qc.invalidateQueries({ queryKey: ['all-schedule-requests'] })
    },
    onError: (e) => { setError(getErrorMessage(e)); setSuccess('') },
  })

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>{title}</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      <Paper variant="outlined" sx={{ p: 3, maxWidth: 720 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Request Type" value={form.request_type} onChange={(e) => setForm({ ...form, request_type: e.target.value })}>
              {requestTypes.map((t) => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Course (optional)" value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })}>
              <MenuItem value="">None</MenuItem>
              {courses.map((c: any) => <MenuItem key={c.id} value={c.id}>{c.code} - {c.name}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Section (optional)" value={form.section_id} onChange={(e) => setForm({ ...form, section_id: e.target.value })}>
              <MenuItem value="">None</MenuItem>
              {sections.map((s: any) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Faculty" value={form.faculty_id} onChange={(e) => setForm({ ...form, faculty_id: e.target.value })}>
              <MenuItem value="">None</MenuItem>
              {faculty.map((f: any) => <MenuItem key={f.id} value={f.id}>{f.full_name}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth type="number" label="Expected Attendees" value={form.student_count} onChange={(e) => setForm({ ...form, student_count: Number(e.target.value) })} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth type="number" label="Duration (hours)" value={form.duration_hours} onChange={(e) => setForm({ ...form, duration_hours: Number(e.target.value) })} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Required Resource Type" value={form.required_resource_type} onChange={(e) => setForm({ ...form, required_resource_type: e.target.value })}>
              <MenuItem value="room">Room</MenuItem><MenuItem value="lab">Lab</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Required Facilities (comma-separated)" value={form.required_facility_names} onChange={(e) => setForm({ ...form, required_facility_names: e.target.value })} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Preferred Day (optional)" value={form.preferred_day_of_week} onChange={(e) => setForm({ ...form, preferred_day_of_week: e.target.value })}>
              <MenuItem value="">Any day</MenuItem>
              {DAYS.map((d, i) => <MenuItem key={d} value={i}>{d}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label="Preferred Start Time (optional)" value={form.preferred_start_slot_index} onChange={(e) => setForm({ ...form, preferred_start_slot_index: e.target.value })}>
              <MenuItem value="">Any time</MenuItem>
              {SLOT_LABELS.map((l, i) => <MenuItem key={l} value={i}>{l}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth type="number" label="Priority (1=highest, 10=lowest)" value={form.base_priority} onChange={(e) => setForm({ ...form, base_priority: Number(e.target.value) })} inputProps={{ min: 1, max: 10 }} />
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth multiline rows={3} label="Reason" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" size="large" onClick={() => create.mutate()}>Submit Request</Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  )
}
