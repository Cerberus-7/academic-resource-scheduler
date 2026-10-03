import { useQuery } from '@tanstack/react-query'
import { Grid, Typography, Paper, Box } from '@mui/material'
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom'
import PendingActionsIcon from '@mui/icons-material/PendingActions'
import SwapHorizIcon from '@mui/icons-material/SwapHoriz'
import EventAvailableIcon from '@mui/icons-material/EventAvailable'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { api } from '../../api/client'
import KpiCard from '../../components/KpiCard'

export default function AdminDashboard() {
  const { data: kpis } = useQuery({ queryKey: ['dashboard-kpis'], queryFn: () => api.get('/analytics/dashboard').then(r => r.data) })
  const { data: utilization } = useQuery({ queryKey: ['utilization'], queryFn: () => api.get('/analytics/utilization').then(r => r.data) })

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Admin Dashboard</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Active Timetable Slots" value={kpis?.total_allocations ?? '—'} icon={<EventAvailableIcon />} color="#1565C0" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Pending Requests" value={kpis?.pending_schedule_requests ?? '—'} icon={<PendingActionsIcon />} color="#B98900" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Pending Shift Approvals" value={kpis?.pending_shift_requests ?? '—'} icon={<SwapHorizIcon />} color="#C62828" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Active Rooms/Labs" value={`${kpis?.active_resources ?? '—'} / ${kpis?.total_resources ?? '—'}`} icon={<MeetingRoomIcon />} color="#2E7D32" />
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Resource Utilization (% of weekly slots used)</Typography>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={utilization ?? []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="code" />
            <YAxis unit="%" />
            <Tooltip />
            <Bar dataKey="utilization_percent" fill="#1D4E89" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Paper>
    </Box>
  )
}
