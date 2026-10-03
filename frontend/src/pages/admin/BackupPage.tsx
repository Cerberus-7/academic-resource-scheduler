import { useRef, useState } from 'react'
import {
  Box, Typography, Paper, Button, Stack, Alert, FormControlLabel, Switch,
  Dialog, DialogTitle, DialogContent, DialogActions, Table, TableBody, TableCell, TableRow, CircularProgress,
} from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import { api, getErrorMessage } from '../../api/client'

export default function BackupPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [clearExisting, setClearExisting] = useState(true)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<Record<string, number> | null>(null)

  async function handleExport() {
    setExporting(true); setError('')
    try {
      const res = await api.get('/backup/export', { responseType: 'blob' })
      const url = window.URL.createObjectURL(res.data)
      const a = document.createElement('a')
      const stamp = new Date().toISOString().replace(/[:.]/g, '-')
      a.href = url
      a.download = `academic-scheduler-backup-${stamp}.json`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  function handleFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      setPendingFile(file)
      setConfirmOpen(true)
    }
  }

  async function handleConfirmImport() {
    if (!pendingFile) return
    setImporting(true); setError(''); setResult(null); setConfirmOpen(false)
    try {
      const formData = new FormData()
      formData.append('file', pendingFile)
      const res = await api.post('/backup/import', formData, {
        params: { clear_existing: clearExisting },
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data.row_counts)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setImporting(false)
      setPendingFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1 }}>Backup &amp; Restore</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Export the entire database to a single local JSON file, or restore from a previously
        exported file. This is a local backup / demo-data feature only — SQLite remains the
        primary database at all times; no cloud storage is used.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {result && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Import complete — {Object.values(result).reduce((a, b) => a + b, 0)} rows restored across {Object.keys(result).length} tables.
        </Alert>
      )}

      <Stack direction="row" spacing={3} flexWrap="wrap">
        <Paper variant="outlined" sx={{ p: 3, width: 360 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Export Backup</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Downloads a JSON file containing every table's current data — users, resources,
            faculty, courses, the full timetable, requests, and logs.
          </Typography>
          <Button
            variant="contained" startIcon={exporting ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}
            onClick={handleExport} disabled={exporting} fullWidth
          >
            {exporting ? 'Exporting…' : 'Download Backup (.json)'}
          </Button>
        </Paper>

        <Paper variant="outlined" sx={{ p: 3, width: 360 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Restore from Backup</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload a previously exported JSON file to restore the database.
          </Typography>
          <FormControlLabel
            control={<Switch checked={clearExisting} onChange={(e) => setClearExisting(e.target.checked)} />}
            label="Clear existing data before restoring"
            sx={{ mb: 1 }}
          />
          <input ref={fileInputRef} type="file" accept="application/json" hidden onChange={handleFilePicked} />
          <Button
            variant="outlined" startIcon={importing ? <CircularProgress size={16} /> : <UploadFileIcon />}
            onClick={() => fileInputRef.current?.click()} disabled={importing} fullWidth
          >
            {importing ? 'Importing…' : 'Choose Backup File…'}
          </Button>
        </Paper>
      </Stack>

      {result && (
        <Paper variant="outlined" sx={{ p: 2, mt: 3, maxWidth: 500 }}>
          <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Rows restored per table</Typography>
          <Table size="small">
            <TableBody>
              {Object.entries(result).filter(([, n]) => n > 0).map(([table, n]) => (
                <TableRow key={table}><TableCell>{table}</TableCell><TableCell align="right">{n}</TableCell></TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningAmberIcon color="warning" /> Confirm Restore
        </DialogTitle>
        <DialogContent>
          <Typography>
            You're about to import <strong>{pendingFile?.name}</strong>.{' '}
            {clearExisting
              ? 'This will PERMANENTLY WIPE all existing data and replace it with the contents of this file.'
              : 'Existing rows will be kept and the file\'s rows will be added alongside them.'}
          </Typography>
          <Typography sx={{ mt: 2 }} color="text.secondary" variant="body2">This action cannot be undone. Continue?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setConfirmOpen(false); setPendingFile(null); if (fileInputRef.current) fileInputRef.current.value = '' }}>Cancel</Button>
          <Button variant="contained" color="warning" onClick={handleConfirmImport}>Yes, Restore</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
