import { useMemo, useState } from 'react'
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TableSortLabel,
  TablePagination, TextField, InputAdornment, Paper, Box,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'

export interface Column<T> {
  key: string
  label: string
  sortable?: boolean
  render?: (row: T) => React.ReactNode
  getValue?: (row: T) => string | number
  searchable?: boolean
}

export default function DataTable<T extends { id: number | string }>({
  columns, rows, defaultSortKey, defaultRowsPerPage = 10, searchPlaceholder = 'Search…', actionsColumn,
}: {
  columns: Column<T>[]
  rows: T[]
  defaultSortKey?: string
  defaultRowsPerPage?: number
  searchPlaceholder?: string
  actionsColumn?: (row: T) => React.ReactNode
}) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState(defaultSortKey ?? columns[0]?.key)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(defaultRowsPerPage)

  const searchableCols = columns.filter((c) => c.searchable !== false)

  const filtered = useMemo(() => {
    if (!search.trim()) return rows
    const q = search.toLowerCase()
    return rows.filter((row) =>
      searchableCols.some((c) => {
        const v = c.getValue ? c.getValue(row) : (row as any)[c.key]
        return String(v ?? '').toLowerCase().includes(q)
      })
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, search])

  const sorted = useMemo(() => {
    const col = columns.find((c) => c.key === sortKey)
    if (!col) return filtered
    const copy = [...filtered]
    copy.sort((a, b) => {
      const va = col.getValue ? col.getValue(a) : (a as any)[col.key]
      const vb = col.getValue ? col.getValue(b) : (b as any)[col.key]
      if (va === vb) return 0
      const result = va > vb ? 1 : -1
      return sortDir === 'asc' ? result : -result
    })
    return copy
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtered, sortKey, sortDir])

  const paged = sorted.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  return (
    <Paper variant="outlined">
      <Box sx={{ p: 1.5 }}>
        <TextField
          size="small" placeholder={searchPlaceholder} value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0) }}
          sx={{ width: 280 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> }}
        />
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((c) => (
                <TableCell key={c.key}>
                  {c.sortable === false ? c.label : (
                    <TableSortLabel active={sortKey === c.key} direction={sortKey === c.key ? sortDir : 'asc'} onClick={() => handleSort(c.key)}>
                      {c.label}
                    </TableSortLabel>
                  )}
                </TableCell>
              ))}
              {actionsColumn && <TableCell />}
            </TableRow>
          </TableHead>
          <TableBody>
            {paged.map((row) => (
              <TableRow key={row.id} hover>
                {columns.map((c) => <TableCell key={c.key}>{c.render ? c.render(row) : (row as any)[c.key]}</TableCell>)}
                {actionsColumn && <TableCell align="right">{actionsColumn(row)}</TableCell>}
              </TableRow>
            ))}
            {paged.length === 0 && (
              <TableRow><TableCell colSpan={columns.length + (actionsColumn ? 1 : 0)} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                {search ? 'No rows match your search.' : 'No data yet.'}
              </TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div" count={sorted.length} page={page} onPageChange={(_, p) => setPage(p)}
        rowsPerPage={rowsPerPage} onRowsPerPageChange={(e) => { setRowsPerPage(Number(e.target.value)); setPage(0) }}
        rowsPerPageOptions={[5, 10, 25, 50]}
      />
    </Paper>
  )
}
