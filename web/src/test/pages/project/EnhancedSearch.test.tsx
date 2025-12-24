import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../utils'
import { EnhancedSearch } from '../../../pages/project/EnhancedSearch'
import { graphitiService } from '../../../services/graphitiService'
import { useParams } from 'react-router-dom'

vi.mock('../../../services/graphitiService', () => ({
    graphitiService: {
        getGraphData: vi.fn(),
        searchByGraphTraversal: vi.fn(),
        searchTemporal: vi.fn(),
        searchWithFacets: vi.fn(),
    }
}))

vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useParams: vi.fn(),
    }
})

describe('EnhancedSearch', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useParams as any).mockReturnValue({ projectId: 'p1' });
    })

    it('renders search mode buttons', () => {
        render(<EnhancedSearch />)
        expect(screen.getByRole('button', { name: 'Semantic Search' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Graph Traversal' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Temporal Search' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Faceted Search' })).toBeInTheDocument()
    })

    it('switches to Graph Traversal mode', () => {
        render(<EnhancedSearch />)
        fireEvent.click(screen.getByRole('button', { name: 'Graph Traversal' }))

        expect(screen.getByText('Start Entity UUID')).toBeInTheDocument()
        expect(screen.getByText('Max Depth (1-5)')).toBeInTheDocument()
    })

    it('performs Graph Traversal search', async () => {
        (graphitiService.searchByGraphTraversal as any).mockResolvedValue({
            results: [{ content: 'Result 1', score: 0.9, metadata: { type: 'entity' }, source: 'graph' }]
        })

        render(<EnhancedSearch />)
        fireEvent.click(screen.getByRole('button', { name: 'Graph Traversal' }))

        fireEvent.change(screen.getByPlaceholderText('entity-uuid-123'), { target: { value: 'uuid-1' } })

        // Find the search button. The icon text 'search' + 'Search' might make strict match fail.
        // We look for the button containing 'Search' that is not one of the mode buttons.
        const searchButton = screen.getAllByRole('button').find(b => b.textContent?.includes('Search') && !b.textContent?.includes('Semantic') && !b.textContent?.includes('Temporal') && !b.textContent?.includes('Faceted') && !b.textContent?.includes('Graph'))
        if (searchButton) fireEvent.click(searchButton)

        await waitFor(() => {
            expect(graphitiService.searchByGraphTraversal).toHaveBeenCalledWith(expect.objectContaining({
                start_entity_uuid: 'uuid-1',
                max_depth: 2
            }))
            expect(screen.getByText('Result 1')).toBeInTheDocument()
        })
    })

    it('performs Temporal Search', async () => {
        (graphitiService.searchTemporal as any).mockResolvedValue({
            results: [{ content: 'Temporal Result', score: 0.8, metadata: { type: 'episode' }, source: 'temporal' }]
        })

        render(<EnhancedSearch />)
        fireEvent.click(screen.getByRole('button', { name: 'Temporal Search' }))

        fireEvent.change(screen.getByPlaceholderText('Enter your search query...'), { target: { value: 'test' } })

        const searchButton = screen.getAllByRole('button').find(b => b.textContent?.includes('Search') && !b.textContent?.includes('Semantic') && !b.textContent?.includes('Temporal') && !b.textContent?.includes('Faceted') && !b.textContent?.includes('Graph'))
        if (searchButton) fireEvent.click(searchButton)

        await waitFor(() => {
            expect(graphitiService.searchTemporal).toHaveBeenCalled()
            expect(screen.getByText('Temporal Result')).toBeInTheDocument()
        })
    })

    it('performs Faceted Search', async () => {
        (graphitiService.searchWithFacets as any).mockResolvedValue({
            results: [{ content: 'Faceted Result', score: 0.7, metadata: { type: 'entity' }, source: 'faceted' }]
        })

        render(<EnhancedSearch />)
        fireEvent.click(screen.getByRole('button', { name: 'Faceted Search' }))

        fireEvent.change(screen.getByPlaceholderText('Person, Organization'), { target: { value: 'Person' } })
        fireEvent.change(screen.getByPlaceholderText('Enter your search query...'), { target: { value: 'test' } })

        const searchButton = screen.getAllByRole('button').find(b => b.textContent?.includes('Search') && !b.textContent?.includes('Semantic') && !b.textContent?.includes('Temporal') && !b.textContent?.includes('Faceted') && !b.textContent?.includes('Graph'))
        if (searchButton) fireEvent.click(searchButton)

        await waitFor(() => {
            expect(graphitiService.searchWithFacets).toHaveBeenCalledWith(expect.objectContaining({
                query: 'test',
                entity_types: ['Person']
            }))
            expect(screen.getByText('Faceted Result')).toBeInTheDocument()
        })
    })
})
