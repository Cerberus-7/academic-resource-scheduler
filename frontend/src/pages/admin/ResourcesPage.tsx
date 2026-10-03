import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Button, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, MenuItem, Stack, Chip, IconButton, Tabs, Tab, Alert,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import BuildIcon from '@mui/icons-material/Build'
import { api, getErrorMessage } from '../../api/client'
import DataTable, { Column } from '../../components/DataTable'

const FACILITY_OPTIONS = ['Projector', 'Smart Board', 'AC', 'Computers', 'Speaker System', 'Whiteboard']
const EMPTY_FORM = { name: '', code: '', resource_type: 'room', building: '', floor: '', capacity: 40, facility_names: [] as string[] }

export default function ResourcesPage() {
  const [tab, setTab] = useState(0)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [maintDialogOpen, setMaintDialogOpen] = useState(false)
  const [error, setError] = useState('')
  const qc = useQueryClient()

  const { data: resources = [] } = useQuery({ queryKey: ['resources-all'], queryFn: () => api.get('/resources').then(r => r.data) })
  const { data: maintenance = [] } = useQuery({ queryKey: ['maintenance'], queryFn: () => api.get('/resources/maintenance').then(r => r.data) })

  const [form, setForm] = useState(EMPTY_FORM)
  const [maintForm, setMaintForm] = useState({ resource_id: '', start_datetime: '', end_datetime: '', reason: '' })

  const createResource = useMutation({
    mutationFn: () => api.post('/resources', form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['resources-all'] }); setDialogOpen(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const updateResource = useMutation({
    mutationFn: () => api.put(`/resources/${editingId}`, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['resources-all'] }); setDialogOpen(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const deactivate = useMutation({
    mutationFn: (id: number) => api.delete(`/resources/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources-all'] }),
  })
  const createMaintenance = useMutation({
    mutationFn: () => api.post('/resources/maintenance', maintForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['maintenance'] }); setMaintDialogOpen(false); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const deleteMaintenance = useMutation({
    mutationFn: (id: number) => api.delete(`/resources/maintenance/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['maintenance'] }),
  })

  function openCreate() {
    setEditingId(null); setForm(EMPTY_FORM); setError(''); setDialogOpen(true)
  }
  function openEdit(r: any) {
    setEditingId(r.id)
    setForm({
      name: r.name, code: r.code, resource_type: r.resource_type, building: r.building,
      floor: r.floor, capacity: r.capacity, facility_names: r.facilities.map((f: any) => f.name),
    })
    setError(''); setDialogOpen(true)
  }

  const resourceColumns: Column<any>[] = [
    { key: 'code', label: 'Code' },
    { key: 'name', label: 'Name' },
    { key: 'resource_type', label: 'Type', render: (r) => <span style={{ textTransform: 'capitalize' }}>{r.resource_type}</span> },
    { key: 'building', label: 'Building' },
    { key: 'capacity', label: 'Capacity' },
    {
      key: 'facilities', label: 'Facilities', sortable: false,
      getValue: (r) => r.facilities.map((f: any) => f.name).join(', '),
      render: (r) => r.facilities.map((f: any) => <Chip key={f.id} label={f.name} size="small" sx={{ mr: 0.5, mb: 0.5 }} />),
    },
    {
      key: 'is_active', label: 'Status', getValue: (r) => (r.is_active ? 'Active' : 'Inactive'),
      render: (r) => <Chip label={r.is_active ? 'Active' : 'Inactive'} color={r.is_active ? 'success' : 'default'} size="small" />,
    },
  ]

  const maintenanceColumns: Column<any>[] = [
    {
      key: 'resource_id', label: 'Resource',
      getValue: (m) => { const r = resources.find((x: any) => x.id === m.resource_id); return r ? `${r.name} (${r.code})` : m.resource_id },
      render: (m) => { const r = resources.find((x: any) => x.id === m.resource_id); return r ? `${r.name} (${r.code})` : m.resource_id },
    },
    { key: 'start_datetime', label: 'From', render: (m) => new Date(m.start_datetime).toLocaleString() },
    { key: 'end_datetime', label: 'To', render: (m) => new Date(m.end_datetime).toLocaleString() },
    { key: 'reason', label: 'Reason' },
  ]

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4">Rooms &amp; Labs</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<BuildIcon />} onClick={() => setMaintDialogOpen(true)}>Add Maintenance Window</Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>Add Room/Lab</Button>
        </Stack>
      </Stack>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Rooms & Labs" />
        <Tab label="Maintenance Windows" />
      </Tabs>

      {tab === 0 && (
        <DataTable
          columns={resourceColumns} rows={resources} defaultSortKey="code" searchPlaceholder="Search rooms/labs…"
          actionsColumn={(r) => (
            <Stack direction="row" spacing={0.5} justifyContent="flex-end">
              <IconButton size="small" onClick={() => openEdit(r)}><EditIcon fontSize="small" /></IconButton>
              {r.is_active && <IconButton size="small" onClick={() => deactivate.mutate(r.id)}><DeleteIcon fontSize="small" /></IconButton>}
            </Stack>
          )}
        />
      )}

      {tab === 1 && (
        <DataTable
          columns={maintenanceColumns} rows={maintenance} defaultSortKey="start_datetime" searchPlaceholder="Search maintenance…"
          actionsColumn={(m) => <IconButton size="small" onClick={() => deleteMaintenance.mutate(m.id)}><DeleteIcon fontSize="small" /></IconButton>}
        />
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? 'Edit Room / Lab' : 'Add Room / Lab'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth />
            <TextField label="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} fullWidth />
            <TextField select label="Type" value={form.resource_type} onChange={(e) => setForm({ ...form, resource_type: e.target.value })} fullWidth>
              <MenuItem value="room">Room</MenuItem>
              <MenuItem value="lab">Lab</MenuItem>
            </TextField>
            <TextField label="Building" value={form.building} onChange={(e) => setForm({ ...form, building: e.target.value })} fullWidth />
            <TextField label="Floor" value={form.floor} onChange={(e) => setForm({ ...form, floor: e.target.value })} fullWidth />
            <TextField label="Capacity" type="number" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })} fullWidth />
            <TextField
              select SelectProps={{ multiple: true }} label="Facilities"
              value={form.facility_names} onChange={(e) => setForm({ ...form, facility_names: e.target.value as any })} fullWidth
            >
              {FACILITY_OPTIONS.map((f) => <MenuItem key={f} value={f}>{f}</MenuItem>)}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => (editingId ? updateResource.mutate() : createResource.mutate())}>Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={maintDialogOpen} onClose={() => setMaintDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Maintenance Window</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField select label="Resource" value={maintForm.resource_id} onChange={(e) => setMaintForm({ ...maintForm, resource_id: e.target.value })} fullWidth>
              {resources.map((r: any) => <MenuItem key={r.id} value={r.id}>{r.name} ({r.code})</MenuItem>)}
            </TextField>
            <TextField label="Start" type="datetime-local" InputLabelProps={{ shrink: true }} value={maintForm.start_datetime} onChange={(e) => setMaintForm({ ...maintForm, start_datetime: e.target.value })} fullWidth />
            <TextField label="End" type="datetime-local" InputLabelProps={{ shrink: true }} value={maintForm.end_datetime} onChange={(e) => setMaintForm({ ...maintForm, end_datetime: e.target.value })} fullWidth />
            <TextField label="Reason" value={maintForm.reason} onChange={(e) => setMaintForm({ ...maintForm, reason: e.target.value })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMaintDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMaintenance.mutate()}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
