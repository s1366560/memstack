import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../utils'
import { SearchPage } from '../../../pages/project/SearchPage'
import { memoryAPI } from '../../../services/api'
import { useParams } from 'react-router-dom'

vi.mock('../../../services/api', () => ({
    memoryAPI: {
        search: vi.fn(),
    }
}))

vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useParams: vi.fn(),
        Link: ({ children, to }: any) => <a href={to}>{children}</a>
    }
})

describe('SearchPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useParams as any).mockReturnValue({ projectId: 'p1' });
    })

    it('renders search input', () => {
        render(<SearchPage />)
        expect(screen.getByPlaceholderText('Search memories by keyword, concept, or ask a question...')).toBeInTheDocument()
    })

    it('performs search', async () => {
        (memoryAPI.search as any).mockResolvedValue({
            results: [
                {
                    id: 'm1',
                    content: 'Memory Content 1',
                    score: 0.9,
                    created_at: new Date().toISOString()
                }
            ]
        })

        render(<SearchPage />)

        fireEvent.change(screen.getByPlaceholderText('Search memories by keyword, concept, or ask a question...'), { target: { value: 'test' } })
        fireEvent.click(screen.getByText('Retrieve'))

        await waitFor(() => {
            expect(memoryAPI.search).toHaveBeenCalledWith('p1', { query: 'test', limit: 20 })
            expect(screen.getByText('Memory Content 1')).toBeInTheDocument()
        })
    })

    it('handles empty results', async () => {
        (memoryAPI.search as any).mockResolvedValue({ results: [] })

        render(<SearchPage />)

        fireEvent.change(screen.getByPlaceholderText('Search memories by keyword, concept, or ask a question...'), { target: { value: 'nothing' } })
        fireEvent.click(screen.getByText('Retrieve'))

        await waitFor(() => {
            expect(screen.getByText('No results found. Try adjusting your query or filters.')).toBeInTheDocument()
        })
    })
})
