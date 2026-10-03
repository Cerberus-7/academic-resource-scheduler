import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Button, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, MenuItem, Stack, Alert, IconButton,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import { api, getErrorMessage } from '../../api/client'
import { DAYS } from '../../types'
import DataTable, { Column } from '../../components/DataTable'

const EMPTY_FORM = { employee_code: '', full_name: '', department: '', designation: '', qualified_course_ids: [] as number[] }

export default function FacultyPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [unavailDialogOpen, setUnavailDialogOpen] = useState(false)
  const [error, setError] = useState('')
  const qc = useQueryClient()

  const { data: faculty = [] } = useQuery({ queryKey: ['faculty'], queryFn: () => api.get('/faculty').then(r => r.data) })
  const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: () => api.get('/courses').then(r => r.data) })
  const { data: unavailability = [] } = useQuery({ queryKey: ['unavailability'], queryFn: () => api.get('/faculty/unavailability').then(r => r.data) })

  const [form, setForm] = useState(EMPTY_FORM)
  const [unavailForm, setUnavailForm] = useState({ faculty_id: '', day_of_week: 0, start_time: '09:00', end_time: '10:00', reason: '' })

  const createFaculty = useMutation({
    mutationFn: () => api.post('/faculty', form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['faculty'] }); setDialogOpen(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const updateFaculty = useMutation({
    mutationFn: () => api.put(`/faculty/${editingId}`, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['faculty'] }); setDialogOpen(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const createUnavail = useMutation({
    mutationFn: () => api.post('/faculty/unavailability', unavailForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['unavailability'] }); setUnavailDialogOpen(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })

  function openCreate() { setEditingId(null); setForm(EMPTY_FORM); setError(''); setDialogOpen(true) }
  function openEdit(f: any) {
    setEditingId(f.id)
    setForm({ employee_code: f.employee_code, full_name: f.full_name, department: f.department, designation: f.designation, qualified_course_ids: [] })
    setError(''); setDialogOpen(true)
  }

  const facultyColumns: Column<any>[] = [
    { key: 'employee_code', label: 'Code' },
    { key: 'full_name', label: 'Name' },
    { key: 'department', label: 'Department' },
    { key: 'designation', label: 'Designation' },
  ]

  const unavailColumns: Column<any>[] = [
    { key: 'faculty_id', label: 'Faculty', getValue: (u) => faculty.find((f: any) => f.id === u.faculty_id)?.full_name ?? u.faculty_id, render: (u) => faculty.find((f: any) => f.id === u.faculty_id)?.full_name ?? u.faculty_id },
    { key: 'day_of_week', label: 'Day', getValue: (u) => DAYS[u.day_of_week], render: (u) => DAYS[u.day_of_week] },
    { key: 'start_time', label: 'Time', getValue: (u) => u.start_time, render: (u) => `${u.start_time} - ${u.end_time}` },
    { key: 'reason', label: 'Reason' },
  ]

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4">Faculty Management</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" onClick={() => setUnavailDialogOpen(true)}>Mark Unavailable</Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>Add Faculty</Button>
        </Stack>
      </Stack>

      <Box sx={{ mb: 3 }}>
        <DataTable
          columns={facultyColumns} rows={faculty} defaultSortKey="full_name" searchPlaceholder="Search faculty…"
          actionsColumn={(f) => <IconButton size="small" onClick={() => openEdit(f)}><EditIcon fontSize="small" /></IconButton>}
        />
      </Box>

      <Typography variant="h6" sx={{ mb: 1 }}>Faculty Unavailability</Typography>
      <DataTable columns={unavailColumns} rows={unavailability} defaultSortKey="faculty_id" searchPlaceholder="Search…" />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? 'Edit Faculty' : 'Add Faculty'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Employee Code" value={form.employee_code} onChange={(e) => setForm({ ...form, employee_code: e.target.value })} fullWidth />
            <TextField label="Full Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} fullWidth />
            <TextField label="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} fullWidth />
            <TextField label="Designation" value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} fullWidth />
            <TextField select SelectProps={{ multiple: true }} label="Qualified Courses" value={form.qualified_course_ids}
              onChange={(e) => setForm({ ...form, qualified_course_ids: e.target.value as any })} fullWidth
              helperText={editingId ? 'Leave empty to keep existing qualifications unchanged' : undefined}>
              {courses.map((c: any) => <MenuItem key={c.id} value={c.id}>{c.code} - {c.name}</MenuItem>)}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => (editingId ? updateFaculty.mutate() : createFaculty.mutate())}>Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={unavailDialogOpen} onClose={() => setUnavailDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Mark Faculty Unavailable</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField select label="Faculty" value={unavailForm.faculty_id} onChange={(e) => setUnavailForm({ ...unavailForm, faculty_id: e.target.value })} fullWidth>
              {faculty.map((f: any) => <MenuItem key={f.id} value={f.id}>{f.full_name}</MenuItem>)}
            </TextField>
            <TextField select label="Day" value={unavailForm.day_of_week} onChange={(e) => setUnavailForm({ ...unavailForm, day_of_week: Number(e.target.value) })} fullWidth>
              {DAYS.map((d, i) => <MenuItem key={d} value={i}>{d}</MenuItem>)}
            </TextField>
            <TextField label="Start Time" type="time" value={unavailForm.start_time} onChange={(e) => setUnavailForm({ ...unavailForm, start_time: e.target.value })} fullWidth />
            <TextField label="End Time" type="time" value={unavailForm.end_time} onChange={(e) => setUnavailForm({ ...unavailForm, end_time: e.target.value })} fullWidth />
            <TextField label="Reason" value={unavailForm.reason} onChange={(e) => setUnavailForm({ ...unavailForm, reason: e.target.value })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUnavailDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createUnavail.mutate()}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
