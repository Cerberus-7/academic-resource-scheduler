import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Box, Typography, Button } from '@mui/material'
import { api } from '../api/client'
import StatusChip from '../components/StatusChip'
import DataTable, { Column } from '../components/DataTable'

export default function MyRequestsPage({ title }: { title: string }) {
  const qc = useQueryClient()
  const { data: requests = [] } = useQuery({
    queryKey: ['my-requests'], queryFn: () => api.get('/schedule-requests', { params: { mine_only: true } }).then(r => r.data),
    refetchInterval: 6000,
  })
  const cancel = useMutation({
    mutationFn: (id: number) => api.post(`/schedule-requests/${id}/cancel`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-requests'] }),
  })

  const columns: Column<any>[] = [
    { key: 'request_type', label: 'Type', render: (r) => <span style={{ textTransform: 'capitalize' }}>{r.request_type.replace(/_/g, ' ')}</span> },
    { key: 'title', label: 'Title' },
    { key: 'base_priority', label: 'Priority' },
    { key: 'status', label: 'Status', render: (r) => <StatusChip status={r.status} /> },
    { key: 'failure_reason', label: 'Failure Reason', sortable: false },
  ]

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>{title}</Typography>
      <DataTable
        columns={columns} rows={requests} defaultSortKey="title" searchPlaceholder="Search requests…"
        actionsColumn={(r) => (r.status === 'pending' ? <Button size="small" color="error" onClick={() => cancel.mutate(r.id)}>Cancel</Button> : null)}
      />
    </Box>
  )
}
