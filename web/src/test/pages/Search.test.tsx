import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../utils'
import { Search } from '../../pages/Search'

// Mock AppLayout
vi.mock('../../components/AppLayout', () => ({
    AppLayout: ({ children, customHeader }: any) => (
        <div>
            {customHeader}
            {children}
        </div>
    ),
    NavigationGroup: () => null
}))

describe('GlobalSearch', () => {
    it('renders search interface', () => {
        render(<Search />)
        expect(screen.getByPlaceholderText('Search resources...')).toBeInTheDocument()
        expect(screen.getByText('Time Range')).toBeInTheDocument()
        expect(screen.getByText('Similarity')).toBeInTheDocument()
    })

    it('updates search query', () => {
        render(<Search />)
        const input = screen.getByPlaceholderText('Search resources...')
        fireEvent.change(input, { target: { value: 'new query' } })
        expect(input).toHaveValue('new query')
    })

    it('renders mock results', () => {
        render(<Search />)
        // Since it uses mock data in the component currently
        expect(screen.getByText(/Results/)).toBeInTheDocument()
    })
})
