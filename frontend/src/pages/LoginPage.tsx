import { useState } from 'react'
import { Box, Paper, TextField, Button, Typography, Alert, MenuItem, Stack, Divider } from '@mui/material'
import SchoolIcon from '@mui/icons-material/School'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../api/client'

const DEMO_ACCOUNTS = [
  { label: 'Administrator', email: 'admin@college.edu', password: 'Admin@123' },
  { label: 'Professor', email: 'professor@college.edu', password: 'Prof@123' },
  { label: 'Event Coordinator', email: 'coordinator@college.edu', password: 'Coord@123' },
  { label: 'Student', email: 'student@college.edu', password: 'Student@123' },
]

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login, loading } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      bgcolor: '#0F2A4A', backgroundImage: 'linear-gradient(135deg, #0F2A4A 0%, #1D4E89 100%)',
    }}>
      <Paper elevation={6} sx={{ p: 5, width: 420, borderRadius: 3 }}>
        <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
          <SchoolIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h5" fontWeight={700} textAlign="center">Academic Resource Scheduling System</Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">Sign in to continue</Typography>
        </Stack>
        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth />
            <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth />
            <Button type="submit" variant="contained" size="large" disabled={loading} fullWidth>
              {loading ? 'Signing in…' : 'Sign In'}
            </Button>
          </Stack>
        </form>
        <Divider sx={{ my: 3 }}>Demo accounts</Divider>
        <Stack spacing={1}>
          {DEMO_ACCOUNTS.map((acc) => (
            <Button
              key={acc.email} variant="outlined" size="small"
              onClick={() => { setEmail(acc.email); setPassword(acc.password) }}
            >
              {acc.label} — {acc.email}
            </Button>
          ))}
        </Stack>
      </Paper>
    </Box>
  )
}
