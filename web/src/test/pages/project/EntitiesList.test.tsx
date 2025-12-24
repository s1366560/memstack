import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../utils'
import { EntitiesList } from '../../../pages/project/EntitiesList'
import { graphitiService } from '../../../services/graphitiService'
import { useParams } from 'react-router-dom'

// Mock services and hooks
vi.mock('../../../services/graphitiService', () => ({
    graphitiService: {
        listEntities: vi.fn(),
        getEntity: vi.fn(),
        getEntityRelationships: vi.fn(),
    }
}))

vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useParams: vi.fn(),
    }
})

describe('EntitiesList', () => {
    const mockEntities = [
        {
            uuid: 'e1',
            name: 'Entity 1',
            entity_type: 'Person',
            summary: 'Summary 1',
        },
        {
            uuid: 'e2',
            name: 'Entity 2',
            entity_type: 'Organization',
            summary: 'Summary 2',
        }
    ]

    beforeEach(() => {
        vi.clearAllMocks();
        (useParams as any).mockReturnValue({ projectId: 'p1' });
        (graphitiService.listEntities as any).mockResolvedValue({
            items: mockEntities,
            total: 2,
            page: 1,
            total_pages: 1
        });
    })

    it('renders entities list', async () => {
        render(<EntitiesList />)

        expect(screen.getByText('Entities')).toBeInTheDocument()

        await waitFor(() => {
            expect(screen.getByText('Entity 1')).toBeInTheDocument()
            expect(screen.getByText('Entity 2')).toBeInTheDocument()
        })
    })

    it('filters by entity type', async () => {
        render(<EntitiesList />)

        await waitFor(() => {
            expect(screen.getByText('Entity 1')).toBeInTheDocument()
        })

        // Find the select element for filtering
        // Note: Implementation details might vary, assuming a standard select or custom dropdown
        // Based on the summary, it's a "Type Filter Dropdown"
        // Let's assume it has a label or placeholder "Filter by type" or similar
        // Or we can query by role 'combobox' if it's a select

        const filterSelect = screen.getByRole('combobox')
        fireEvent.change(filterSelect, { target: { value: 'Person' } })

        // Should re-fetch with filter
        await waitFor(() => {
            expect(graphitiService.listEntities).toHaveBeenCalledWith(expect.objectContaining({
                entity_type: 'Person'
            }))
        })
    })

    it('shows entity details on click', async () => {
        (graphitiService.getEntityRelationships as any).mockResolvedValue({
            relationships: []
        })

        render(<EntitiesList />)

        await waitFor(() => {
            expect(screen.getByText('Entity 1')).toBeInTheDocument()
        })

        fireEvent.click(screen.getByText('Entity 1'))

        expect(screen.getByText('Entity Details')).toBeInTheDocument()
        expect(screen.getAllByText('Entity 1').length).toBeGreaterThan(0) // Header + List item
    })

    it('handles empty state', async () => {
        (graphitiService.listEntities as any).mockResolvedValue({
            items: [],
            total: 0,
            page: 1,
            total_pages: 0
        })

        render(<EntitiesList />)

        await waitFor(() => {
            expect(screen.getByText('No entities found')).toBeInTheDocument()
        })
    })

    it('handles loading error', async () => {
        (graphitiService.listEntities as any).mockRejectedValue(new Error('Failed to fetch'))

        render(<EntitiesList />)

        await waitFor(() => {
            expect(screen.getByText('Failed to load entities')).toBeInTheDocument()
        })
    })
})
