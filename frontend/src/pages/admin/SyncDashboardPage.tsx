import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Paper, Grid, List, ListItem, ListItemText, Chip, Alert } from '@mui/material'
import KpiCard from '../../components/KpiCard'
import LockIcon from '@mui/icons-material/Lock'
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty'
import BoltIcon from '@mui/icons-material/Bolt'
import { api } from '../../api/client'

export default function SyncDashboardPage() {
  const { data } = useQuery({ queryKey: ['sync-dashboard'], queryFn: () => api.get('/sync/dashboard').then(r => r.data), refetchInterval: 2000 })

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1 }}>Concurrency &amp; Synchronization Dashboard</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        threading.Lock guards the read-check-commit critical section for every timetable write.
        threading.Semaphore bounds concurrent CP-SAT solver jobs to {data?.max_concurrent_jobs ?? '—'} at a time.
        Neither represents a physical room or lab.
      </Alert>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <KpiCard title="Active Solver Workers" value={data?.active_workers ?? '—'} icon={<BoltIcon />} color="#1565C0" />
        </Grid>
        <Grid item xs={12} sm={4}>
          <KpiCard title="Waiting Worker Jobs" value={data?.waiting_workers ?? '—'} icon={<HourglassEmptyIcon />} color="#B98900" />
        </Grid>
        <Grid item xs={12} sm={4}>
          <KpiCard title="Lock Contention Events" value={data?.lock_contention_events ?? '—'} icon={<LockIcon />} color="#C62828" />
        </Grid>
      </Grid>
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>Recent Concurrent Activity</Typography>
        <List dense>
          {data?.recent_activity.map((a: any, i: number) => (
            <ListItem key={i} divider>
              <ListItemText
                primary={<Chip size="small" label={a.event.replace(/_/g, ' ')} />}
                secondary={`${a.detail} — ${new Date(a.timestamp).toLocaleTimeString()}`}
              />
            </ListItem>
          ))}
          {(!data || data.recent_activity.length === 0) && <Typography color="text.secondary" variant="body2">No activity yet.</Typography>}
        </List>
      </Paper>
    </Box>
  )
}
