import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UserManager } from '../../components/UserManager'
import { useTenantStore } from '../../stores/tenant'
import { useProjectStore } from '../../stores/project'

vi.mock('../../stores/tenant', () => ({
    useTenantStore: vi.fn()
}))

vi.mock('../../stores/project', () => ({
    useProjectStore: vi.fn()
}))

describe('UserManager', () => {
    beforeEach(() => {
        vi.clearAllMocks()
            ; (useTenantStore as any).mockReturnValue({
                currentTenant: { id: 'tenant-1', name: 'Tenant 1' }
            })
            ; (useProjectStore as any).mockReturnValue({
                currentProject: { id: 'project-1', name: 'Project 1' }
            })
    })

    it('renders tenant context empty state', () => {
         (useTenantStore as any).mockReturnValue({ currentTenant: null })
        render(<UserManager context="tenant" />)
        expect(screen.getByText('请先选择工作空间')).toBeInTheDocument()
    })

    it('renders project context empty state', () => {
         (useProjectStore as any).mockReturnValue({ currentProject: null })
        render(<UserManager context="project" />)
        expect(screen.getByText('请先选择项目')).toBeInTheDocument()
    })

    it('renders tenant users', async () => {
        render(<UserManager context="tenant" />)

        // The component uses hardcoded mock data for now, so we can expect it to be rendered
        await waitFor(() => {
            expect(screen.getAllByText('管理员').length).toBeGreaterThan(0)
            expect(screen.getAllByText('普通用户').length).toBeGreaterThan(0)
        })
    })

    it('renders project users', async () => {
        render(<UserManager context="project" />)

        await waitFor(() => {
            expect(screen.getAllByText('项目管理员').length).toBeGreaterThan(0)
            // "查看者" appears in dropdown option too
            expect(screen.getAllByText('查看者').length).toBeGreaterThan(0)
        })
    })

    it('opens invite modal', () => {
        render(<UserManager context="tenant" />)
        // "邀请用户" might appear multiple times (header button, empty state button)
        // We want the one that is a button
        const buttons = screen.getAllByText('邀请用户')
        fireEvent.click(buttons[0])
        expect(screen.getByText('发送邀请')).toBeInTheDocument()
    })
})
