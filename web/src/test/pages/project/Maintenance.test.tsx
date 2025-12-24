import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../utils'
import { Maintenance } from '../../../pages/project/Maintenance'
import { graphitiService } from '../../../services/graphitiService'
import { useParams } from 'react-router-dom'

vi.mock('../../../services/graphitiService', () => ({
    graphitiService: {
        getGraphStats: vi.fn(),
        exportData: vi.fn(),
    }
}))

vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useParams: vi.fn(),
    }
})

// Mock fetch for direct API calls in Maintenance component
globalThis.fetch = vi.fn()

describe('Maintenance', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useParams as any).mockReturnValue({ projectId: 'p1' });
        (graphitiService.getGraphStats as any).mockResolvedValue({
            entity_count: 100,
            episodic_count: 50,
            community_count: 5,
            edge_count: 200
        });
        (globalThis.fetch as any).mockResolvedValue({
            json: () => Promise.resolve({
                recommendations: []
            })
        });
    })

    it('renders graph statistics', async () => {
        render(<Maintenance />)

        await waitFor(() => {
            expect(screen.getByText('100')).toBeInTheDocument() // Entities
            expect(screen.getByText('50')).toBeInTheDocument()  // Episodes
            expect(screen.getByText('5')).toBeInTheDocument()   // Communities
        })
    })

    it('handles incremental refresh', async () => {
        (globalThis.fetch as any).mockResolvedValueOnce({
            json: () => Promise.resolve({ recommendations: [] }) // Initial status
        }).mockResolvedValueOnce({
            json: () => Promise.resolve({ episodes_processed: 10 }) // Refresh result
        });

        render(<Maintenance />)

        const refreshBtn = screen.getAllByText('Refresh')[0] // There might be multiple "Refresh" texts
        fireEvent.click(refreshBtn)

        expect(screen.getByText('Refreshing...')).toBeInTheDocument()
        
        await waitFor(() => {
            expect(screen.getByText('Refreshed 10 episodes')).toBeInTheDocument()
        })
    })

    it('handles deduplication check', async () => {
        (globalThis.fetch as any).mockResolvedValueOnce({
            json: () => Promise.resolve({ recommendations: [] })
        }).mockResolvedValueOnce({
            json: () => Promise.resolve({ duplicates_found: 5 })
        });

        render(<Maintenance />)

        const checkBtns = screen.getAllByText('Check')
        fireEvent.click(checkBtns[0]) // Deduplicate Check

        await waitFor(() => {
            expect(screen.getByText('Found 5 potential duplicates')).toBeInTheDocument()
        })
    })

    it('handles data export', async () => {
        (graphitiService.exportData as any).mockResolvedValue({ some: 'data' })
        
        // Mock URL.createObjectURL
        globalThis.URL.createObjectURL = vi.fn()
        globalThis.URL.revokeObjectURL = vi.fn()

        render(<Maintenance />)

        fireEvent.click(screen.getByText('Export'))

        await waitFor(() => {
            expect(graphitiService.exportData).toHaveBeenCalled()
            expect(screen.getByText('Data exported successfully')).toBeInTheDocument()
        })
    })
})
