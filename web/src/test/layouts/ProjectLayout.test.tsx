
import { describe, it, expect, vi } from 'vitest'
import { screen, render } from '../utils'
import { ProjectLayout } from '../../layouts/ProjectLayout'

vi.mock('../../components/WorkspaceSwitcher', () => ({
    WorkspaceSwitcher: () => <div>MockSwitcher</div>
}))

describe('ProjectLayout', () => {
    it('renders project navigation items', () => {
        render(<ProjectLayout />, { route: '/project/p1' })

        expect(screen.getByText('Overview')).toBeInTheDocument()
        expect(screen.getByText('Memories')).toBeInTheDocument()
        expect(screen.getByText('Graph')).toBeInTheDocument()
    })
})
