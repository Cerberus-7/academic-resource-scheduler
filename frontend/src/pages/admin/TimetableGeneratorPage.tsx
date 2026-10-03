import { useState } from 'react'
import { Box, Typography, Paper, Button, Stack, Alert, TextField, FormControlLabel, Switch, CircularProgress } from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { api, getErrorMessage } from '../../api/client'

export default function TimetableGeneratorPage() {
  const [clearExisting, setClearExisting] = useState(true)
  const [maxSeconds, setMaxSeconds] = useState(30)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  async function handleGenerate() {
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await api.post('/timetable/generate', { clear_existing: clearExisting, max_solve_seconds: maxSeconds })
      setResult(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1 }}>Timetable Generator</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Uses OR-Tools CP-SAT as the sole authority to place every course session onto a room/lab, day,
        and time slot — enforcing capacity, room type, equipment, faculty qualification, faculty
        availability, and maintenance-window constraints, with no double-booking of any room, lab,
        faculty member, or student section.
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, maxWidth: 520 }}>
        <Stack spacing={2}>
          <FormControlLabel
            control={<Switch checked={clearExisting} onChange={(e) => setClearExisting(e.target.checked)} />}
            label="Clear existing timetable before generating"
          />
          <TextField
            label="Max solve time (seconds)" type="number" value={maxSeconds}
            onChange={(e) => setMaxSeconds(Number(e.target.value))}
          />
          <Button
            variant="contained" size="large" startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <AutoAwesomeIcon />}
            onClick={handleGenerate} disabled={loading}
          >
            {loading ? 'Solving with CP-SAT…' : 'Generate Timetable'}
          </Button>
        </Stack>
      </Paper>

      {error && <Alert severity="error" sx={{ mt: 3, maxWidth: 520 }}>{error}</Alert>}
      {result && (
        <Alert severity={result.success ? 'success' : 'warning'} sx={{ mt: 3, maxWidth: 520 }}>
          <strong>{result.solve_status}</strong> — {result.message}
          <br />
          {result.success && `${result.allocations_created} allocations created in ${result.solve_time_seconds}s.`}
        </Alert>
      )}
    </Box>
  )
}
