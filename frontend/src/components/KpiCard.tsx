import { Card, CardContent, Typography, Box } from '@mui/material'
import { ReactNode } from 'react'

export default function KpiCard({ title, value, icon, color = 'primary.main' }: {
  title: string; value: string | number; icon: ReactNode; color?: string
}) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{
          width: 48, height: 48, borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center',
          bgcolor: color, color: '#fff', flexShrink: 0,
        }}>
          {icon}
        </Box>
        <Box>
          <Typography variant="h5" fontWeight={700}>{value}</Typography>
          <Typography variant="body2" color="text.secondary">{title}</Typography>
        </Box>
      </CardContent>
    </Card>
  )
}
