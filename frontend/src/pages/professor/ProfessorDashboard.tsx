import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Grid, Paper } from '@mui/material'
import EventAvailableIcon from '@mui/icons-material/EventAvailable'
import PendingActionsIcon from '@mui/icons-material/PendingActions'
import SwapHorizIcon from '@mui/icons-material/SwapHoriz'
import { api } from '../../api/client'
import { useAuth } from '../../hooks/useAuth'
import KpiCard from '../../components/KpiCard'

export default function ProfessorDashboard() {
  const { user } = useAuth()
  const { data: faculty = [] } = useQuery({ queryKey: ['faculty'], queryFn: () => api.get('/faculty').then(r => r.data) })
  const myFaculty = faculty.find((f: any) => f.user_id === user?.id)

  const { data: myRequests = [] } = useQuery({ queryKey: ['my-requests'], queryFn: () => api.get('/schedule-requests', { params: { mine_only: true } }).then(r => r.data) })
  const { data: myShifts = [] } = useQuery({
    queryKey: ['shift-requests', myFaculty?.id], queryFn: () => api.get('/shift-requests', { params: { faculty_id: myFaculty?.id } }).then(r => r.data),
    enabled: !!myFaculty,
  })

  const pendingShifts = myShifts.filter((s: any) => ['pending', 'under_discussion', 'alternative_proposed'].includes(s.status))

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1 }}>Welcome, {user?.full_name}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Here's what's happening with your schedule.</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <KpiCard title="My Pending Requests" value={myRequests.filter((r: any) => r.status === 'pending').length} icon={<PendingActionsIcon />} color="#B98900" />
        </Grid>
        <Grid item xs={12} sm={4}>
          <KpiCard title="Shift Requests Awaiting Me" value={pendingShifts.length} icon={<SwapHorizIcon />} color="#C62828" />
        </Grid>
        <Grid item xs={12} sm={4}>
          <KpiCard title="Total Requests Submitted" value={myRequests.length} icon={<EventAvailableIcon />} color="#1565C0" />
        </Grid>
      </Grid>
    </Box>
  )
}
