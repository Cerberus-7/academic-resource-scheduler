import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Paper, Alert, Grid, Table, TableBody, TableCell, TableHead, TableRow,
  Button, TextField, Stack, Chip, Dialog, DialogTitle, DialogContent, DialogActions, MenuItem,
} from '@mui/material'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import { api, getErrorMessage } from '../../api/client'

const RESOURCE_TYPES = ['lecture_room_units', 'computer_lab_units', 'faculty_slot_units', 'projector_units', 'special_equipment_units']

export default function OsSimulationPage() {
  const qc = useQueryClient()
  const [error, setError] = useState('')
  const [lastMessage, setLastMessage] = useState<{ text: string; severity: 'success' | 'warning' } | null>(null)
  const [initDialog, setInitDialog] = useState(false)
  const [initForm, setInitForm] = useState({
    total_resources: '10,5,8,4,3',
    processes: 'P1:4,2,3,1,1\nP2:3,1,2,2,1\nP3:5,2,3,1,1',
    allocation: 'P1:2,1,1,0,0\nP2:1,0,1,1,0\nP3:2,1,1,0,0',
  })
  const [reqForm, setReqForm] = useState({ process_name: '', vector: '' })
  const [relForm, setRelForm] = useState({ process_name: '', vector: '' })
  const [addProcForm, setAddProcForm] = useState({ process_name: '', max_demand: '' })
  const [reduceForm, setReduceForm] = useState({ resource_index: 0, reduced_units: 1, reason: 'maintenance simulation' })

  const { data: state } = useQuery({ queryKey: ['banker-state'], queryFn: () => api.get('/banker/state').then(r => r.data) })
  const { data: history = [] } = useQuery({ queryKey: ['banker-history'], queryFn: () => api.get('/banker/history').then(r => r.data) })

  function parseVectorMap(text: string) {
    const out: Record<string, number[]> = {}
    text.split('\n').filter(Boolean).forEach((line) => {
      const [name, vec] = line.split(':')
      out[name.trim()] = vec.split(',').map((n) => Number(n.trim()))
    })
    return out
  }

  const invalidate = () => { qc.invalidateQueries({ queryKey: ['banker-state'] }); qc.invalidateQueries({ queryKey: ['banker-history'] }) }

  const REJECTION_KEYWORDS = ['exceeds', 'unsafe', 'cannot', 'Cannot', 'Unknown', 'Invalid', 'already exists', 'Unexpected', 'rejected']
  function showResult(message: string) {
    const isRejected = REJECTION_KEYWORDS.some((kw) => message.includes(kw))
    setLastMessage({ text: message, severity: isRejected ? 'warning' : 'success' })
  }

  const init = useMutation({
    mutationFn: () => api.post('/banker/init', {
      total_resources: initForm.total_resources.split(',').map(Number),
      processes: parseVectorMap(initForm.processes),
      allocation: parseVectorMap(initForm.allocation),
    }),
    onSuccess: () => { invalidate(); setInitDialog(false); setError(''); setLastMessage(null) },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const request = useMutation({
    mutationFn: () => api.post('/banker/request', { process_name: reqForm.process_name, request_vector: reqForm.vector.split(',').map(Number) }),
    onSuccess: (res) => { invalidate(); setError(''); showResult(res.data.message) },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const release = useMutation({
    mutationFn: () => api.post('/banker/release', { process_name: relForm.process_name, release_vector: relForm.vector.split(',').map(Number) }),
    onSuccess: (res) => { invalidate(); setError(''); showResult(res.data.message) },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const addProcess = useMutation({
    mutationFn: () => api.post('/banker/add-process', { process_name: addProcForm.process_name, max_demand: addProcForm.max_demand.split(',').map(Number) }),
    onSuccess: (res) => { invalidate(); setError(''); showResult(res.data.message) },
    onError: (e) => setError(getErrorMessage(e)),
  })
  const reduceCapacity = useMutation({
    mutationFn: () => api.post('/banker/reduce-capacity', reduceForm),
    onSuccess: (res) => { invalidate(); setError(''); showResult(res.data.message) },
    onError: (e) => setError(getErrorMessage(e)),
  })

  const processNames = state ? Object.keys(state.max_matrix) : []
  const hasProcesses = processNames.length > 0

  // If the current selection no longer exists (state was reset/reinitialized
  // with different process names, or the backend lost its in-memory state
  // after a restart), MUI's Select would otherwise silently show blank.
  // Keep the selection in sync instead, defaulting to the first process.
  useEffect(() => {
    if (!hasProcesses) {
      if (reqForm.process_name) setReqForm((f) => ({ ...f, process_name: '' }))
      if (relForm.process_name) setRelForm((f) => ({ ...f, process_name: '' }))
      return
    }
    if (!processNames.includes(reqForm.process_name)) {
      setReqForm((f) => ({ ...f, process_name: processNames[0] }))
    }
    if (!processNames.includes(relForm.process_name)) {
      setRelForm((f) => ({ ...f, process_name: processNames[0] }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processNames.join(',')])

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1 }}>Operating Systems Resource Safety Simulation</Typography>
      <Alert severity="warning" icon={<WarningAmberIcon />} sx={{ mb: 3, fontWeight: 600 }}>
        Separate from Final Timetable Allocation — this page simulates the Classical and Dynamic Banker's
        Algorithm over abstract resource units for OS-education purposes only. It never approves real
        room/time/faculty bookings; that decision is made exclusively by OR-Tools CP-SAT.
      </Alert>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {lastMessage && <Alert severity={lastMessage.severity} sx={{ mb: 2 }} onClose={() => setLastMessage(null)}>{lastMessage.text}</Alert>}

      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button variant="contained" onClick={() => setInitDialog(true)}>Initialize / Reset State</Button>
        {state && hasProcesses && <Chip label={state.is_safe ? `SAFE — sequence: ${state.safe_sequence.join(' → ')}` : 'UNSAFE STATE'} color={state.is_safe ? 'success' : 'error'} />}
      </Stack>

      {state && !hasProcesses && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No Banker state is loaded yet (this resets whenever the backend server restarts, since it's
          kept in memory only). Click <strong>Initialize / Reset State</strong> above to load the
          default P1/P2/P3 example — the Process dropdowns below will populate once that's done.
        </Alert>
      )}

      {state && hasProcesses && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>Available Vector</Typography>
              <Table size="small">
                <TableHead><TableRow>{RESOURCE_TYPES.map((t) => <TableCell key={t}>{t}</TableCell>)}</TableRow></TableHead>
                <TableBody><TableRow>{state.available.map((v: number, i: number) => <TableCell key={i}>{v}</TableCell>)}</TableRow></TableBody>
              </Table>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>Max / Allocation / Need Matrices</Typography>
              <Table size="small">
                <TableHead><TableRow><TableCell>Process</TableCell><TableCell>Max</TableCell><TableCell>Allocation</TableCell><TableCell>Need</TableCell></TableRow></TableHead>
                <TableBody>
                  {processNames.map((p) => (
                    <TableRow key={p}>
                      <TableCell>{p}</TableCell>
                      <TableCell>{state.max_matrix[p].join(', ')}</TableCell>
                      <TableCell>{state.allocation_matrix[p].join(', ')}</TableCell>
                      <TableCell>{state.need_matrix[p].join(', ')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>History Log</Typography>
              <Table size="small">
                <TableHead><TableRow><TableCell>Event</TableCell><TableCell>Safe?</TableCell><TableCell>Time</TableCell></TableRow></TableHead>
                <TableBody>
                  {history.slice(0, 10).map((h: any) => (
                    <TableRow key={h.id}>
                      <TableCell>{h.event}</TableCell>
                      <TableCell><Chip size="small" label={h.is_safe ? 'safe' : 'unsafe'} color={h.is_safe ? 'success' : 'error'} /></TableCell>
                      <TableCell>{new Date(h.created_at).toLocaleTimeString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>

          <Grid item xs={12} md={5}>
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Request Resources</Typography>
              <Stack spacing={1}>
                <TextField select size="small" label="Process" value={reqForm.process_name} onChange={(e) => setReqForm({ ...reqForm, process_name: e.target.value })}>
                  {processNames.map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
                </TextField>
                <TextField size="small" label="Request vector (comma-separated, 5 values)" value={reqForm.vector} onChange={(e) => setReqForm({ ...reqForm, vector: e.target.value })} />
                <Button variant="contained" size="small" disabled={!reqForm.process_name || !reqForm.vector.trim()} onClick={() => request.mutate()}>Request</Button>
              </Stack>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Release Resources</Typography>
              <Stack spacing={1}>
                <TextField select size="small" label="Process" value={relForm.process_name} onChange={(e) => setRelForm({ ...relForm, process_name: e.target.value })}>
                  {processNames.map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
                </TextField>
                <TextField size="small" label="Release vector" value={relForm.vector} onChange={(e) => setRelForm({ ...relForm, vector: e.target.value })} />
                <Button variant="outlined" size="small" disabled={!relForm.process_name || !relForm.vector.trim()} onClick={() => release.mutate()}>Release</Button>
              </Stack>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Dynamic: Add Process at Runtime</Typography>
              <Stack spacing={1}>
                <TextField size="small" label="New process name" value={addProcForm.process_name} onChange={(e) => setAddProcForm({ ...addProcForm, process_name: e.target.value })} />
                <TextField size="small" label="Max demand vector" value={addProcForm.max_demand} onChange={(e) => setAddProcForm({ ...addProcForm, max_demand: e.target.value })} />
                <Button variant="outlined" size="small" disabled={!addProcForm.process_name.trim() || !addProcForm.max_demand.trim()} onClick={() => addProcess.mutate()}>Add Process</Button>
              </Stack>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Dynamic: Reduce Capacity (Maintenance Simulation)</Typography>
              <Stack spacing={1}>
                <TextField select size="small" label="Resource type" value={reduceForm.resource_index} onChange={(e) => setReduceForm({ ...reduceForm, resource_index: Number(e.target.value) })}>
                  {RESOURCE_TYPES.map((t, i) => <MenuItem key={t} value={i}>{t}</MenuItem>)}
                </TextField>
                <TextField size="small" type="number" label="Units to take offline" value={reduceForm.reduced_units} onChange={(e) => setReduceForm({ ...reduceForm, reduced_units: Number(e.target.value) })} />
                <Button variant="outlined" color="warning" size="small" onClick={() => reduceCapacity.mutate()}>Reduce Capacity</Button>
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      )}

      <Dialog open={initDialog} onClose={() => setInitDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Initialize Banker State</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Total resources (5 comma-separated values)" value={initForm.total_resources} onChange={(e) => setInitForm({ ...initForm, total_resources: e.target.value })} fullWidth />
            <TextField label="Processes (name:v1,v2,v3,v4,v5 per line)" value={initForm.processes} onChange={(e) => setInitForm({ ...initForm, processes: e.target.value })} fullWidth multiline rows={3} />
            <TextField label="Allocation (name:v1,v2,v3,v4,v5 per line)" value={initForm.allocation} onChange={(e) => setInitForm({ ...initForm, allocation: e.target.value })} fullWidth multiline rows={3} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInitDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => init.mutate()}>Initialize</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
