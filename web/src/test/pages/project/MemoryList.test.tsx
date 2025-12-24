
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, render, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { MemoryList } from '../../../pages/project/MemoryList'
import { memoryAPI } from '../../../services/api'

vi.mock('../../../services/api')

describe('MemoryList', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    const renderWithRouter = (ui: React.ReactElement, { route = '/' } = {}) => {
        return render(
            <MemoryRouter initialEntries={[route]}>
                <Routes>
                    <Route path="/project/:projectId" element={ui} />
                </Routes>
            </MemoryRouter>
        )
    }

    it('renders list of memories', async () => {
        vi.mocked(memoryAPI.list).mockResolvedValue({
            memories: [
                { id: 'm1', title: 'Memory 1', content: 'Content 1', created_at: '2023-01-01' },
            ]
        })

        renderWithRouter(<MemoryList />, { route: '/project/p1' })

        await waitFor(() => {
            expect(screen.getByText('Memory 1')).toBeInTheDocument()
        })
    })
})
