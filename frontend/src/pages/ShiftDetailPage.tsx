import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Paper, Stack, Chip, Button, TextField, List, ListItem, ListItemText,
  Divider, Alert, RadioGroup, FormControlLabel, Radio, MenuItem, Grid,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import { api, getErrorMessage } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import StatusChip from '../components/StatusChip'
import { DAYS, SLOT_LABELS } from '../types'

export default function ShiftDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const qc = useQueryClient()
  const [message, setMessage] = useState('')
  const [selectedAlt, setSelectedAlt] = useState<number | ''>('')
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [proposeMode, setProposeMode] = useState(false)
  const [newAlt, setNewAlt] = useState({ resource_id: '', day_of_week: 0, start_slot_index: 0, duration_hours: 1 })

  const { data: shift } = useQuery({ queryKey: ['shift', id], queryFn: () => api.get(`/shift-requests/${id}`).then(r => r.data) })
  const { data: discussion = [] } = useQuery({
    queryKey: ['discussion', id], queryFn: () => api.get(`/shift-requests/${id}/discussion`).then(r => r.data),
    refetchInterval: 4000,
  })
  const { data: resources = [] } = useQuery({ queryKey: ['resources-all'], queryFn: () => api.get('/resources').then(r => r.data) })

  const sendMessage = useMutation({
    mutationFn: () => api.post(`/shift-requests/${id}/discussion`, { message }),
    onSuccess: () => { setMessage(''); qc.invalidateQueries({ queryKey: ['discussion', id] }); qc.invalidateQueries({ queryKey: ['shift', id] }) },
  })

  const takeAction = useMutation({
    mutationFn: (payload: any) => api.post(`/shift-requests/${id}/action`, payload),
    onSuccess: () => { setError(''); qc.invalidateQueries({ queryKey: ['shift', id] }); qc.invalidateQueries({ queryKey: ['shift-requests'] }) },
    onError: (e) => setError(getErrorMessage(e)),
  })

  if (!shift) return <Typography>Loading…</Typography>

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Typography variant="h4">Shift Request #{shift.id}</Typography>
        <StatusChip status={shift.status} />
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={700}>Details</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}><strong>Reason:</strong> {shift.reason_code.replace(/_/g, ' ')} — {shift.reason_text}</Typography>
            <Typography variant="body2"><strong>Base priority:</strong> {shift.base_priority}</Typography>
            <Typography variant="body2"><strong>Original allocation ID:</strong> {shift.original_allocation_id}</Typography>
            <Typography variant="body2"><strong>Deadline:</strong> {shift.decision_deadline ? new Date(shift.decision_deadline).toLocaleString() : '—'}</Typography>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>Suggested Alternatives (CP-SAT validated)</Typography>
            {shift.alternatives.length === 0 && <Typography color="text.secondary" variant="body2">No alternatives proposed yet.</Typography>}
            <RadioGroup value={selectedAlt} onChange={(e) => setSelectedAlt(Number(e.target.value))}>
              {shift.alternatives.map((a: any) => {
                const r = resources.find((x: any) => x.id === a.resource_id)
                return (
                  <Paper key={a.id} variant="outlined" sx={{ p: 1.5, mb: 1, borderColor: a.is_cp_sat_valid ? 'success.main' : 'error.main' }}>
                    <FormControlLabel
                      disabled={!a.is_cp_sat_valid}
                      value={a.id}
                      control={<Radio />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {r ? `${r.name} (${r.code})` : a.resource_id} — {DAYS[a.day_of_week]} {SLOT_LABELS[a.start_slot_index]} ({a.duration_hours}h)
                          </Typography>
                          <Typography variant="caption" color={a.is_cp_sat_valid ? 'success.main' : 'error.main'}>
                            {a.is_cp_sat_valid ? '✓ ' : '✗ '}{a.validation_message}
                          </Typography>
                        </Box>
                      }
                    />
                  </Paper>
                )
              })}
            </RadioGroup>

            {user?.id === shift.affected_faculty_id || user?.role === 'admin' ? (
              <Stack spacing={1} sx={{ mt: 2 }}>
                <TextField label="Comment (optional)" size="small" value={comment} onChange={(e) => setComment(e.target.value)} />
                <Stack direction="row" spacing={1}>
                  <Button
                    variant="contained" color="success" disabled={!selectedAlt}
                    onClick={() => takeAction.mutate({ action: 'approve', alternative_id: selectedAlt, comment })}
                  >
                    Approve Selected
                  </Button>
                  <Button variant="outlined" color="error" onClick={() => takeAction.mutate({ action: 'reject', comment })}>
                    Reject
                  </Button>
                  <Button variant="text" onClick={() => setProposeMode(!proposeMode)}>Propose Another Slot</Button>
                </Stack>

                {proposeMode && (
                  <Paper variant="outlined" sx={{ p: 2, mt: 1 }}>
                    <Stack spacing={2}>
                      <TextField select label="Room/Lab" size="small" value={newAlt.resource_id} onChange={(e) => setNewAlt({ ...newAlt, resource_id: e.target.value })}>
                        {resources.map((r: any) => <MenuItem key={r.id} value={r.id}>{r.name} ({r.code})</MenuItem>)}
                      </TextField>
                      <TextField select label="Day" size="small" value={newAlt.day_of_week} onChange={(e) => setNewAlt({ ...newAlt, day_of_week: Number(e.target.value) })}>
                        {DAYS.map((d, i) => <MenuItem key={d} value={i}>{d}</MenuItem>)}
                      </TextField>
                      <TextField select label="Start Time" size="small" value={newAlt.start_slot_index} onChange={(e) => setNewAlt({ ...newAlt, start_slot_index: Number(e.target.value) })}>
                        {SLOT_LABELS.map((l, i) => <MenuItem key={l} value={i}>{l}</MenuItem>)}
                      </TextField>
                      <TextField label="Duration (hours)" size="small" type="number" value={newAlt.duration_hours} onChange={(e) => setNewAlt({ ...newAlt, duration_hours: Number(e.target.value) })} />
                      <Button
                        variant="contained"
                        onClick={() => takeAction.mutate({
                          action: 'propose_alternative',
                          new_alternative: { resource_id: Number(newAlt.resource_id), day_of_week: newAlt.day_of_week, start_slot_index: newAlt.start_slot_index, duration_hours: newAlt.duration_hours },
                          comment,
                        })}
                      >
                        Submit for CP-SAT Validation
                      </Button>
                    </Stack>
                  </Paper>
                )}
              </Stack>
            ) : null}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 480 }}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>Discussion</Typography>
            <List sx={{ flexGrow: 1, overflowY: 'auto' }}>
              {discussion.map((m: any) => (
                <ListItem key={m.id} alignItems="flex-start" disableGutters>
                  <ListItemText
                    primary={<Typography variant="body2" fontWeight={700}>{m.sender_name}</Typography>}
                    secondary={<>
                      <Typography variant="body2">{m.message}</Typography>
                      <Typography variant="caption" color="text.secondary">{new Date(m.created_at).toLocaleString()}</Typography>
                    </>}
                  />
                </ListItem>
              ))}
              {discussion.length === 0 && <Typography color="text.secondary" variant="body2">No messages yet — start the discussion.</Typography>}
            </List>
            <Divider sx={{ my: 1 }} />
            <Stack direction="row" spacing={1}>
              <TextField fullWidth size="small" placeholder="Type a message…" value={message} onChange={(e) => setMessage(e.target.value)} />
              <Button variant="contained" endIcon={<SendIcon />} onClick={() => message.trim() && sendMessage.mutate()}>Send</Button>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
