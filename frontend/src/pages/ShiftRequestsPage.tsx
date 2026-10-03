import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import StatusChip from '../components/StatusChip'
import DataTable, { Column } from '../components/DataTable'

export default function ShiftRequestsPage({ title, basePath, facultyOnly }: {
  title: string
  basePath: string
  facultyOnly?: number
}) {
  const navigate = useNavigate()
  const { data: shifts = [] } = useQuery({
    queryKey: ['shift-requests', facultyOnly],
    queryFn: () => api.get('/shift-requests', { params: { faculty_id: facultyOnly } }).then(r => r.data),
    refetchInterval: 6000,
  })

  const columns: Column<any>[] = [
    { key: 'id', label: 'ID', render: (s) => `#${s.id}` },
    { key: 'reason_code', label: 'Reason', render: (s) => <span style={{ textTransform: 'capitalize' }}>{s.reason_code.replace(/_/g, ' ')}</span> },
    { key: 'base_priority', label: 'Priority' },
    { key: 'status', label: 'Status', render: (s) => <StatusChip status={s.status} /> },
    { key: 'alternatives', label: 'Alternatives', sortable: false, getValue: (s) => s.alternatives?.length ?? 0, render: (s) => s.alternatives?.length ?? 0 },
    { key: 'decision_deadline', label: 'Deadline', render: (s) => (s.decision_deadline ? new Date(s.decision_deadline).toLocaleString() : '—') },
  ]

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>{title}</Typography>
      <DataTable
        columns={columns} rows={shifts} defaultSortKey="id" searchPlaceholder="Search shift requests…"
        actionsColumn={(s) => <Button size="small" onClick={() => navigate(`${basePath}/${s.id}`)}>Open</Button>}
      />
    </Box>
  )
}
