import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  Box, Typography, Paper, Grid, TextField, MenuItem, Button, Table, TableBody, TableCell,
  TableHead, TableRow, Chip, Stack,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { api } from '../api/client'
import { DAYS, AvailabilityResult } from '../types'
import StatusChip from '../components/StatusChip'

export default function AvailabilitySearchPage({ title }: { title: string }) {
  const [params, setParams] = useState({ day_of_week: 0, start_time: '09:00', duration_hours: 1, min_capacity: 0, resource_type: '', facility_names: '' })
  const [results, setResults] = useState<AvailabilityResult[]>([])

  const search = useMutation({
    mutationFn: () => api.get('/availability/search', { params: { ...params, resource_type: params.resource_type || undefined } }).then(r => r.data),
    onSuccess: (data) => setResults(data),
  })

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>{title}</Typography>
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={6} sm={2}>
            <TextField select fullWidth size="small" label="Day" value={params.day_of_week} onChange={(e) => setParams({ ...params, day_of_week: Number(e.target.value) })}>
              {DAYS.map((d, i) => <MenuItem key={d} value={i}>{d}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField fullWidth size="small" type="time" label="Start Time" value={params.start_time} onChange={(e) => setParams({ ...params, start_time: e.target.value })} InputLabelProps={{ shrink: true }} />
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField fullWidth size="small" type="number" label="Duration (h)" value={params.duration_hours} onChange={(e) => setParams({ ...params, duration_hours: Number(e.target.value) })} />
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField fullWidth size="small" type="number" label="Min Capacity" value={params.min_capacity} onChange={(e) => setParams({ ...params, min_capacity: Number(e.target.value) })} />
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField select fullWidth size="small" label="Type" value={params.resource_type} onChange={(e) => setParams({ ...params, resource_type: e.target.value })}>
              <MenuItem value="">Room or Lab</MenuItem><MenuItem value="room">Room</MenuItem><MenuItem value="lab">Lab</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={6} sm={2}>
            <Button fullWidth variant="contained" startIcon={<SearchIcon />} onClick={() => search.mutate()}>Search</Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Resource</TableCell><TableCell>Type</TableCell><TableCell>Capacity</TableCell>
              <TableCell>Facilities</TableCell><TableCell>Status</TableCell><TableCell>Available From</TableCell>
              <TableCell>Available Until</TableCell><TableCell>Max Continuous</TableCell><TableCell>Next Booking</TableCell><TableCell>Suitable?</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.map((r) => (
              <TableRow key={r.resource_id} hover sx={{ opacity: r.is_suitable ? 1 : 0.6 }}>
                <TableCell>{r.name} ({r.code})</TableCell>
                <TableCell sx={{ textTransform: 'capitalize' }}>{r.resource_type}</TableCell>
                <TableCell>{r.capacity}</TableCell>
                <TableCell>{r.facilities.map((f) => <Chip key={f} label={f} size="small" sx={{ mr: 0.5 }} />)}</TableCell>
                <TableCell><StatusChip status={r.status} /></TableCell>
                <TableCell>{r.available_from}</TableCell>
                <TableCell>{r.available_until}</TableCell>
                <TableCell>{r.max_continuous_hours}h</TableCell>
                <TableCell>{r.next_booking ?? '—'}</TableCell>
                <TableCell>{r.is_suitable ? <Chip label="Yes" color="success" size="small" /> : <Chip label="No" size="small" />}</TableCell>
              </TableRow>
            ))}
            {results.length === 0 && <TableRow><TableCell colSpan={10} align="center">Run a search to see availability.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  )
}
