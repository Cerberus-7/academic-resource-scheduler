import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DataTable, { Column } from '../DataTable'

interface Row { id: number; name: string; score: number }
const rows: Row[] = [
  { id: 1, name: 'Banana', score: 3 },
  { id: 2, name: 'Apple', score: 5 },
  { id: 3, name: 'Cherry', score: 1 },
]
const columns: Column<Row>[] = [
  { key: 'name', label: 'Name' },
  { key: 'score', label: 'Score' },
]

describe('DataTable', () => {
  it('renders all rows by default, sorted by the first column ascending', () => {
    render(<DataTable columns={columns} rows={rows} />)
    const cells = screen.getAllByRole('row').slice(1).map((r) => r.textContent)
    expect(cells[0]).toContain('Apple')
    expect(cells[1]).toContain('Banana')
    expect(cells[2]).toContain('Cherry')
  })

  it('filters rows via the search box', () => {
    render(<DataTable columns={columns} rows={rows} searchPlaceholder="Search…" />)
    fireEvent.change(screen.getByPlaceholderText('Search…'), { target: { value: 'cherry' } })
    expect(screen.getByText('Cherry')).toBeInTheDocument()
    expect(screen.queryByText('Banana')).not.toBeInTheDocument()
  })

  it('shows an empty state when search matches nothing', () => {
    render(<DataTable columns={columns} rows={rows} searchPlaceholder="Search…" />)
    fireEvent.change(screen.getByPlaceholderText('Search…'), { target: { value: 'zzz' } })
    expect(screen.getByText('No rows match your search.')).toBeInTheDocument()
  })

  it('re-sorts descending on second click of the same column header', () => {
    render(<DataTable columns={columns} rows={rows} />)
    fireEvent.click(screen.getByText('Score'))
    fireEvent.click(screen.getByText('Score'))
    const cells = screen.getAllByRole('row').slice(1).map((r) => r.textContent)
    expect(cells[0]).toContain('Apple') // score 5, highest first on desc
  })

  it('paginates and respects rows-per-page', () => {
    const many = Array.from({ length: 12 }, (_, i) => ({ id: i, name: `Item ${i}`, score: i }))
    render(<DataTable columns={columns} rows={many} defaultRowsPerPage={5} />)
    expect(screen.getAllByRole('row')).toHaveLength(6) // header + 5 rows
  })
})
