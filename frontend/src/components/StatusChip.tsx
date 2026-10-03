import { Chip } from '@mui/material'
import { STATUS_COLORS } from '../theme/theme'

export default function StatusChip({ status }: { status: string }) {
  const color = STATUS_COLORS[status?.toLowerCase()] ?? 'default'
  return <Chip label={status?.replace(/_/g, ' ')} color={color} size="small" sx={{ textTransform: 'capitalize' }} />
}
