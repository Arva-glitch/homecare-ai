import { fireEvent, render, screen } from '@testing-library/react'
import { ConfirmDialog, EmptyState, HealthBar, Markdown, RiskBadge } from '../components/ui'
import MiniCalendar from '../components/MiniCalendar'

describe('UI components', () => {
  it('renders risk badges and unassessed state', () => {
    render(<><RiskBadge risk="Critical" /><RiskBadge /></>)
    expect(screen.getByText('Critical')).toBeInTheDocument()
    expect(screen.getByText('Not assessed')).toBeInTheDocument()
  })
  it('shows the rounded health score', () => {
    render(<HealthBar score={72.6} />)
    expect(screen.getByText('73')).toBeInTheDocument()
  })
  it('renders markdown bold and lists safely', () => {
    const { container } = render(<Markdown text={'**Possible causes**\n- Dirty filter\n- Low gas\n1. Clean it\n<script>x</script>'} />)
    expect(container.querySelector('strong').textContent).toBe('Possible causes')
    expect(container.querySelectorAll('ul li')).toHaveLength(2)
    expect(container.querySelectorAll('ol li')).toHaveLength(1)
    expect(container.querySelector('script')).toBeNull()
  })
  it('confirm dialog calls handlers', () => {
    const onConfirm = vi.fn(); const onCancel = vi.fn()
    render(<ConfirmDialog open message="Delete it?" confirmLabel="Delete" onConfirm={onConfirm} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('Delete'))
    fireEvent.click(screen.getByText('Cancel'))
    expect(onConfirm).toHaveBeenCalledOnce()
    expect(onCancel).toHaveBeenCalledOnce()
  })
  it('empty state shows action', () => {
    render(<EmptyState title="Nothing here" action={<button>Add</button>} />)
    expect(screen.getByText('Add')).toBeInTheDocument()
  })
  it('calendar highlights event days', () => {
    const now = new Date(); now.setHours(10)
    render(<MiniCalendar events={[{ id: 1, title: 'AC service', scheduled_at: now.toISOString() }]} />)
    expect(screen.getByTitle('AC service')).toBeInTheDocument()
  })
})
