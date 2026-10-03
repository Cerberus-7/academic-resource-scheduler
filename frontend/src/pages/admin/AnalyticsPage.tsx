import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Paper, Grid } from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import { api } from '../../api/client'

export default function AnalyticsPage() {
  const { data } = useQuery({ queryKey: ['scheduler-metrics'], queryFn: () => api.get('/analytics/scheduler-metrics').then(r => r.data) })

  const compareData = data ? [
    { metric: 'Avg Wait (s)', 'Priority + Aging': data.priority_aging.avg_wait, 'Round Robin': data.round_robin.avg_wait },
    { metric: 'Max Wait (s)', 'Priority + Aging': data.priority_aging.max_wait, 'Round Robin': data.round_robin.max_wait },
    { metric: 'Completion %', 'Priority + Aging': data.priority_aging.completion_rate, 'Round Robin': data.round_robin.completion_rate },
  ] : []

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Analytics &amp; Reports</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Priority+Aging vs Round Robin</Typography>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={compareData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Priority + Aging" fill="#1D4E89" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Round Robin" fill="#C89B3C" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Starvation Prevention</Typography>
            <Typography variant="body2" color="text.secondary">Est. max wait without aging</Typography>
            <Typography variant="h5" fontWeight={700}>{data?.starvation_prevention.max_wait_without_aging_estimate ?? '—'}s</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Actual max wait with aging</Typography>
            <Typography variant="h5" fontWeight={700} color="success.main">{data?.starvation_prevention.max_wait_with_aging_actual ?? '—'}s</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
