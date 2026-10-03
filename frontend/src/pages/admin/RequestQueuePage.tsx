import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Box, Typography, Paper, Table, TableBody, TableCell, TableHead, TableRow, Button, Stack, Chip, Alert } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import FastForwardIcon from '@mui/icons-material/FastForward'
import { api } from '../../api/client'
import StatusChip from '../../components/StatusChip'
import DataTable, { Column } from '../../components/DataTable'

export default function RequestQueuePage() {
  const qc = useQueryClient()
  const { data: queue = [] } = useQuery({
    queryKey: ['request-queue'], queryFn: () => api.get('/schedule-requests/queue').then(r => r.data),
    refetchInterval: 5000,
  })
  const { data: allRequests = [] } = useQuery({
    queryKey: ['all-schedule-requests'], queryFn: () => api.get('/schedule-requests').then(r => r.data),
    refetchInterval: 5000,
  })

  const processNext = useMutation({
    mutationFn: () => api.post('/schedule-requests/process-next'),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['request-queue'] }); qc.invalidateQueries({ queryKey: ['all-schedule-requests'] }) },
  })
  const processAll = useMutation({
    mutationFn: () => api.post('/schedule-requests/process-all'),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['request-queue'] }); qc.invalidateQueries({ queryKey: ['all-schedule-requests'] }) },
  })

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4">Request Queue</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<PlayArrowIcon />} onClick={() => processNext.mutate()} disabled={queue.length === 0}>
            Process Next
          </Button>
          <Button variant="contained" startIcon={<FastForwardIcon />} onClick={() => processAll.mutate()} disabled={queue.length === 0}>
            Process All Pending
          </Button>
        </Stack>
      </Stack>

      <Alert severity="info" sx={{ mb: 2 }}>
        Priority Scheduling + Aging decide processing order below (lower effective priority = served first;
        aging lowers a request's effective priority the longer it waits). Round Robin breaks exact ties.
        OR-Tools CP-SAT alone decides whether — and where — each request actually fits on the timetable.
      </Alert>

      <Typography variant="h6" sx={{ mb: 1 }}>Pending Queue (ordered)</Typography>
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell><TableCell>Type</TableCell><TableCell>Title</TableCell>
              <TableCell>Base Priority</TableCell><TableCell>Effective Priority</TableCell>
              <TableCell>Waiting (s)</TableCell><TableCell>Arrival</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {queue.map((r: any, idx: number) => (
              <TableRow key={r.id} hover>
                <TableCell>{idx + 1}</TableCell>
                <TableCell sx={{ textTransform: 'capitalize' }}>{r.request_type.replace(/_/g, ' ')}</TableCell>
                <TableCell>{r.title}</TableCell>
                <TableCell>{r.base_priority}</TableCell>
                <TableCell><Chip label={r.effective_priority?.toFixed(1)} size="small" color={idx === 0 ? 'error' : 'default'} /></TableCell>
                <TableCell>{r.waiting_seconds?.toFixed(0)}</TableCell>
                <TableCell>{new Date(r.arrival_time).toLocaleTimeString()}</TableCell>
              </TableRow>
            ))}
            {queue.length === 0 && <TableRow><TableCell colSpan={7} align="center">No pending requests.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Paper>

      <Typography variant="h6" sx={{ mb: 1 }}>All Requests (history)</Typography>
      <DataTable
        columns={[
          { key: 'request_type', label: 'Type', render: (r: any) => <span style={{ textTransform: 'capitalize' }}>{r.request_type.replace(/_/g, ' ')}</span> },
          { key: 'title', label: 'Title' },
          { key: 'status', label: 'Status', render: (r: any) => <StatusChip status={r.status} /> },
          { key: 'failure_reason', label: 'Failure Reason', sortable: false },
        ] as Column<any>[]}
        rows={allRequests} defaultSortKey="title" searchPlaceholder="Search request history…"
      />
    </Box>
  )
}
