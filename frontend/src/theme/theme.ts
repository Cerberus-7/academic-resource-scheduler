import { createTheme } from '@mui/material/styles'

export const getAppTheme = (mode: 'light' | 'dark') =>
  createTheme({
    palette: {
      mode,
      primary: { main: '#0F2A4A', light: '#1D4E89', dark: '#081A30', contrastText: '#fff' },
      secondary: { main: '#C89B3C' },
      background: mode === 'light'
        ? { default: '#F4F6F8', paper: '#FFFFFF' }
        : { default: '#0B1220', paper: '#111A2B' },
      success: { main: '#2E7D32' },
      warning: { main: '#B98900' },
      error: { main: '#C62828' },
      info: { main: '#1565C0' },
      grey: { 500: '#64748B' },
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily: ['Inter', 'Roboto', 'Segoe UI', 'Arial', 'sans-serif'].join(','),
      h4: { fontWeight: 700 },
      h5: { fontWeight: 700 },
      h6: { fontWeight: 600 },
    },
    components: {
      MuiAppBar: { styleOverrides: { root: { boxShadow: 'none', borderBottom: '1px solid rgba(0,0,0,0.08)' } } },
      MuiCard: { styleOverrides: { root: { borderRadius: 14 } } },
      MuiButton: { styleOverrides: { root: { textTransform: 'none', fontWeight: 600, borderRadius: 8 } } },
      MuiChip: { styleOverrides: { root: { fontWeight: 600 } } },
    },
  })

export const STATUS_COLORS: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  approved: 'success', active: 'success', available: 'success', applied: 'success',
  pending: 'warning', under_discussion: 'warning', alternative_proposed: 'warning', occupied: 'warning',
  rejected: 'error', failed: 'error', conflict: 'error', maintenance: 'error', unavailable: 'error',
  scheduled: 'info', information: 'info',
  cancelled: 'default', expired: 'default', moved: 'default',
}
