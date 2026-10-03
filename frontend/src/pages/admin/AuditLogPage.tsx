import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Chip } from '@mui/material'
import { api } from '../../api/client'
import DataTable, { Column } from '../../components/DataTable'

export default function AuditLogPage() {
  const { data: logs = [] } = useQuery({ queryKey: ['audit-logs'], queryFn: () => api.get('/analytics/audit-logs').then(r => r.data) })

  const columns: Column<any>[] = [
    { key: 'created_at', label: 'Time', render: (l) => new Date(l.created_at).toLocaleString() },
    { key: 'action', label: 'Action' },
    { key: 'entity_type', label: 'Entity', getValue: (l) => `${l.entity_type} ${l.entity_id ?? ''}`, render: (l) => `${l.entity_type} ${l.entity_id ? `#${l.entity_id}` : ''}` },
    { key: 'details', label: 'Details', sortable: false, render: (l) => <span style={{ maxWidth: 400, display: 'inline-block' }}>{l.details}</span> },
    { key: 'is_override', label: 'Override', getValue: (l) => (l.is_override ? 'OVERRIDE' : ''), render: (l) => l.is_override && <Chip label="OVERRIDE" color="error" size="small" /> },
  ]

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>Audit Log</Typography>
      <DataTable columns={columns} rows={logs} defaultSortKey="created_at" defaultRowsPerPage={25} searchPlaceholder="Search audit log…" />
    </Box>
  )
}
