import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Button, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, MenuItem, Stack, Alert, Tabs, Tab, Switch, FormControlLabel, IconButton,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import { api, getErrorMessage } from '../../api/client'
import DataTable, { Column } from '../../components/DataTable'

const EMPTY_COURSE = { code: '', name: '', credits: 3, requires_lab: false }
const EMPTY_SECTION = { name: '', course_id: '', student_count: 60, semester: 1 }

export default function CoursesPage() {
  const [tab, setTab] = useState(0)
  const [courseDialog, setCourseDialog] = useState(false)
  const [sectionDialog, setSectionDialog] = useState(false)
  const [sessionDialog, setSessionDialog] = useState(false)
  const [editingCourseId, setEditingCourseId] = useState<number | null>(null)
  const [editingSectionId, setEditingSectionId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const qc = useQueryClient()

  const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: () => api.get('/courses').then(r => r.data) })
  const { data: sections = [] } = useQuery({ queryKey: ['sections'], queryFn: () => api.get('/courses/sections').then(r => r.data) })
  const { data: sessions = [] } = useQuery({ queryKey: ['sessions'], queryFn: () => api.get('/courses/sessions').then(r => r.data) })
  const { data: faculty = [] } = useQuery({ queryKey: ['faculty'], queryFn: () => api.get('/faculty').then(r => r.data) })

  const [courseForm, setCourseForm] = useState(EMPTY_COURSE)
  const [sectionForm, setSectionForm] = useState(EMPTY_SECTION)
  const [sessionForm, setSessionForm] = useState({
    section_id: '', faculty_id: '', session_type: 'lecture', duration_hours: 1,
    sessions_per_week: 1, required_resource_type: 'room', required_facility_names: '',
  })

  const createCourse = useMutation({
    mutationFn: () => api.post('/courses', courseForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['courses'] }); setCourseDialog(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const updateCourse = useMutation({
    mutationFn: () => api.put(`/courses/${editingCourseId}`, courseForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['courses'] }); setCourseDialog(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const createSection = useMutation({
    mutationFn: () => api.post('/courses/sections', sectionForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sections'] }); setSectionDialog(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const updateSection = useMutation({
    mutationFn: () => api.put(`/courses/sections/${editingSectionId}`, sectionForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sections'] }); setSectionDialog(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const createSession = useMutation({
    mutationFn: () => api.post('/courses/sessions', sessionForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sessions'] }); setSessionDialog(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const deleteSession = useMutation({
    mutationFn: (id: number) => api.delete(`/courses/sessions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions'] }),
  })

  function openCreateCourse() { setEditingCourseId(null); setCourseForm(EMPTY_COURSE); setError(''); setCourseDialog(true) }
  function openEditCourse(c: any) { setEditingCourseId(c.id); setCourseForm({ code: c.code, name: c.name, credits: c.credits, requires_lab: c.requires_lab }); setError(''); setCourseDialog(true) }
  function openCreateSection() { setEditingSectionId(null); setSectionForm(EMPTY_SECTION); setError(''); setSectionDialog(true) }
  function openEditSection(s: any) { setEditingSectionId(s.id); setSectionForm({ name: s.name, course_id: s.course_id, student_count: s.student_count, semester: s.semester }); setError(''); setSectionDialog(true) }

  const courseColumns: Column<any>[] = [
    { key: 'code', label: 'Code' }, { key: 'name', label: 'Name' }, { key: 'credits', label: 'Credits' },
    { key: 'requires_lab', label: 'Requires Lab', getValue: (c) => (c.requires_lab ? 'Yes' : 'No'), render: (c) => (c.requires_lab ? 'Yes' : 'No') },
  ]
  const sectionColumns: Column<any>[] = [
    { key: 'name', label: 'Section' },
    { key: 'course_id', label: 'Course', getValue: (s) => courses.find((c: any) => c.id === s.course_id)?.code ?? '', render: (s) => courses.find((c: any) => c.id === s.course_id)?.code ?? '' },
    { key: 'student_count', label: 'Students' }, { key: 'semester', label: 'Semester' },
  ]
  const sessionColumns: Column<any>[] = [
    { key: 'section_id', label: 'Section', getValue: (s) => sections.find((x: any) => x.id === s.section_id)?.name ?? '', render: (s) => sections.find((x: any) => x.id === s.section_id)?.name ?? '' },
    { key: 'faculty_id', label: 'Faculty', getValue: (s) => faculty.find((x: any) => x.id === s.faculty_id)?.full_name ?? '', render: (s) => faculty.find((x: any) => x.id === s.faculty_id)?.full_name ?? '' },
    { key: 'session_type', label: 'Type', render: (s) => <span style={{ textTransform: 'capitalize' }}>{s.session_type}</span> },
    { key: 'duration_hours', label: 'Duration', render: (s) => `${s.duration_hours}h` },
    { key: 'sessions_per_week', label: 'Per Week' },
    { key: 'required_resource_type', label: 'Resource', render: (s) => <span style={{ textTransform: 'capitalize' }}>{s.required_resource_type}</span> },
  ]

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>Courses &amp; Sections</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Courses" /><Tab label="Sections" /><Tab label="Weekly Sessions" />
      </Tabs>

      {tab === 0 && (
        <>
          <Button variant="contained" startIcon={<AddIcon />} sx={{ mb: 2 }} onClick={openCreateCourse}>Add Course</Button>
          <DataTable
            columns={courseColumns} rows={courses} defaultSortKey="code" searchPlaceholder="Search courses…"
            actionsColumn={(c) => <IconButton size="small" onClick={() => openEditCourse(c)}><EditIcon fontSize="small" /></IconButton>}
          />
        </>
      )}

      {tab === 1 && (
        <>
          <Button variant="contained" startIcon={<AddIcon />} sx={{ mb: 2 }} onClick={openCreateSection}>Add Section</Button>
          <DataTable
            columns={sectionColumns} rows={sections} defaultSortKey="name" searchPlaceholder="Search sections…"
            actionsColumn={(s) => <IconButton size="small" onClick={() => openEditSection(s)}><EditIcon fontSize="small" /></IconButton>}
          />
        </>
      )}

      {tab === 2 && (
        <>
          <Button variant="contained" startIcon={<AddIcon />} sx={{ mb: 2 }} onClick={() => setSessionDialog(true)}>Add Weekly Session</Button>
          <DataTable
            columns={sessionColumns} rows={sessions} defaultSortKey="section_id" searchPlaceholder="Search sessions…"
            actionsColumn={(s) => <IconButton size="small" onClick={() => deleteSession.mutate(s.id)}><DeleteIcon fontSize="small" /></IconButton>}
          />
        </>
      )}

      <Dialog open={courseDialog} onClose={() => setCourseDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingCourseId ? 'Edit Course' : 'Add Course'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Code" value={courseForm.code} onChange={(e) => setCourseForm({ ...courseForm, code: e.target.value })} fullWidth />
            <TextField label="Name" value={courseForm.name} onChange={(e) => setCourseForm({ ...courseForm, name: e.target.value })} fullWidth />
            <TextField label="Credits" type="number" value={courseForm.credits} onChange={(e) => setCourseForm({ ...courseForm, credits: Number(e.target.value) })} fullWidth />
            <FormControlLabel control={<Switch checked={courseForm.requires_lab} onChange={(e) => setCourseForm({ ...courseForm, requires_lab: e.target.checked })} />} label="Requires Lab" />
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setCourseDialog(false)}>Cancel</Button><Button variant="contained" onClick={() => (editingCourseId ? updateCourse.mutate() : createCourse.mutate())}>Save</Button></DialogActions>
      </Dialog>

      <Dialog open={sectionDialog} onClose={() => setSectionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingSectionId ? 'Edit Section' : 'Add Section'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Section Name" value={sectionForm.name} onChange={(e) => setSectionForm({ ...sectionForm, name: e.target.value })} fullWidth />
            <TextField select label="Course" value={sectionForm.course_id} onChange={(e) => setSectionForm({ ...sectionForm, course_id: e.target.value })} fullWidth>
              {courses.map((c: any) => <MenuItem key={c.id} value={c.id}>{c.code} - {c.name}</MenuItem>)}
            </TextField>
            <TextField label="Student Count" type="number" value={sectionForm.student_count} onChange={(e) => setSectionForm({ ...sectionForm, student_count: Number(e.target.value) })} fullWidth />
            <TextField label="Semester" type="number" value={sectionForm.semester} onChange={(e) => setSectionForm({ ...sectionForm, semester: Number(e.target.value) })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setSectionDialog(false)}>Cancel</Button><Button variant="contained" onClick={() => (editingSectionId ? updateSection.mutate() : createSection.mutate())}>Save</Button></DialogActions>
      </Dialog>

      <Dialog open={sessionDialog} onClose={() => setSessionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Weekly Session</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField select label="Section" value={sessionForm.section_id} onChange={(e) => setSessionForm({ ...sessionForm, section_id: e.target.value })} fullWidth>
              {sections.map((s: any) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
            </TextField>
            <TextField select label="Faculty" value={sessionForm.faculty_id} onChange={(e) => setSessionForm({ ...sessionForm, faculty_id: e.target.value })} fullWidth>
              {faculty.map((f: any) => <MenuItem key={f.id} value={f.id}>{f.full_name}</MenuItem>)}
            </TextField>
            <TextField select label="Session Type" value={sessionForm.session_type} onChange={(e) => setSessionForm({ ...sessionForm, session_type: e.target.value })} fullWidth>
              <MenuItem value="lecture">Lecture</MenuItem><MenuItem value="lab">Lab</MenuItem><MenuItem value="tutorial">Tutorial</MenuItem>
            </TextField>
            <TextField label="Duration (hours)" type="number" value={sessionForm.duration_hours} onChange={(e) => setSessionForm({ ...sessionForm, duration_hours: Number(e.target.value) })} fullWidth />
            <TextField label="Sessions per Week" type="number" value={sessionForm.sessions_per_week} onChange={(e) => setSessionForm({ ...sessionForm, sessions_per_week: Number(e.target.value) })} fullWidth />
            <TextField select label="Required Resource Type" value={sessionForm.required_resource_type} onChange={(e) => setSessionForm({ ...sessionForm, required_resource_type: e.target.value })} fullWidth>
              <MenuItem value="room">Room</MenuItem><MenuItem value="lab">Lab</MenuItem>
            </TextField>
            <TextField label="Required Facilities (comma-separated)" value={sessionForm.required_facility_names} onChange={(e) => setSessionForm({ ...sessionForm, required_facility_names: e.target.value })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setSessionDialog(false)}>Cancel</Button><Button variant="contained" onClick={() => createSession.mutate()}>Save</Button></DialogActions>
      </Dialog>
    </Box>
  )
}
