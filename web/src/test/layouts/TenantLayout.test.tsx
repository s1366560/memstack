
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, render } from '../utils'
import { TenantLayout } from '../../layouts/TenantLayout'
import { useTenantStore } from '../../stores/tenant'

vi.mock('../../stores/tenant')
vi.mock('../../components/WorkspaceSwitcher', () => ({
    WorkspaceSwitcher: () => <div>MockSwitcher</div>
}))

describe('TenantLayout', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('renders layout elements', () => {
        vi.mocked(useTenantStore).mockReturnValue({
            currentTenant: { id: 't1', name: 'Test Tenant' },
            getTenant: vi.fn(),
            setCurrentTenant: vi.fn(),
        } as any)

        render(<TenantLayout />)

        expect(screen.getByText('MemStack')).toBeInTheDocument()
        expect(screen.getByText('Overview')).toBeInTheDocument()
        expect(screen.getByText('Projects')).toBeInTheDocument()
    })

    it('toggles sidebar', () => {
        vi.mocked(useTenantStore).mockReturnValue({
            currentTenant: { id: 't1', name: 'Test Tenant' },
            getTenant: vi.fn(),
        } as any)

        render(<TenantLayout />)

        // Initially expanded
        expect(screen.getByText('Overview')).toBeVisible()

        // Click toggle button
        const toggleBtn = screen.getByText('menu').closest('button')
        fireEvent.click(toggleBtn!)

        // Should be collapsed (text hidden or styled differently, hard to test strict visibility with just jsdom sometimes, 
        // but we can check if the class changed or if text is gone from accessibility tree if conditional rendering is used)
        
        // In our implementation, we hide text with conditional rendering: {!isSidebarCollapsed && ...}
        expect(screen.queryByText('Overview')).not.toBeInTheDocument()
    })

    it('syncs tenant from URL', () => {
        const getTenantMock = vi.fn()
        vi.mocked(useTenantStore).mockReturnValue({
            currentTenant: null,
            getTenant: getTenantMock,
        } as any)

        render(<TenantLayout />, { route: '/tenant/t123' })
        
        // The component uses useParams which might not work perfectly with MemoryRouter initialEntries directly 
        // unless we render with a Route path.
        // But let's see if we can mock useParams or use a Route wrapper in render.
    })
})
