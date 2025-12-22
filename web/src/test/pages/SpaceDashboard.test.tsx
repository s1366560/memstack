import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SpaceDashboard } from '../../pages/SpaceDashboard';
import { useTenantStore } from '../../stores/tenant';
import { useProjectStore } from '../../stores/project';

// Mock AppLayout
vi.mock('../../components/AppLayout', () => ({
  AppLayout: ({ children, title }: any) => (
    <div data-testid="app-layout">
      <h1>{title}</h1>
      {children}
    </div>
  ),
}));

// Mock ProjectCreateModal
vi.mock('../../components/ProjectCreateModal', () => ({
  ProjectCreateModal: ({ isOpen, onClose }: any) => (
    isOpen ? <div data-testid="create-project-modal"><button onClick={onClose}>Close</button></div> : null
  ),
}));

// Mock stores
vi.mock('../../stores/tenant', () => ({
  useTenantStore: vi.fn(),
}));
vi.mock('../../stores/project', () => ({
  useProjectStore: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ spaceId: '123' }),
  };
});

describe('SpaceDashboard', () => {
  const mockGetTenant = vi.fn();
  const mockListProjects = vi.fn();
  const mockSetCurrentProject = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useTenantStore as any).mockReturnValue({
      currentTenant: { id: '123', name: 'Test Tenant' },
      getTenant: mockGetTenant,
    });
    (useProjectStore as any).mockReturnValue({
      projects: [],
      listProjects: mockListProjects,
      setCurrentProject: mockSetCurrentProject,
    });
  });

  it('should load initial data', () => {
    render(
      <BrowserRouter>
        <SpaceDashboard />
      </BrowserRouter>
    );

    expect(mockGetTenant).toHaveBeenCalledWith('123');
    expect(mockListProjects).toHaveBeenCalledWith('123');
  });

  it('should render project list', () => {
    const mockProjects = [
      { id: 'p1', name: 'Project 1', created_at: new Date().toISOString() },
      { id: 'p2', name: 'Project 2', created_at: new Date().toISOString() },
    ];

    (useProjectStore as any).mockReturnValue({
      projects: mockProjects,
      listProjects: mockListProjects,
      setCurrentProject: mockSetCurrentProject,
    });

    render(
      <BrowserRouter>
        <SpaceDashboard />
      </BrowserRouter>
    );

    expect(screen.getByText('Project 1')).toBeInTheDocument();
    expect(screen.getByText('Project 2')).toBeInTheDocument();
  });

  it('should navigate to project dashboard', () => {
    const mockProject = { id: 'p1', name: 'Project 1', created_at: new Date().toISOString() };
    (useProjectStore as any).mockReturnValue({
      projects: [mockProject],
      listProjects: mockListProjects,
      setCurrentProject: mockSetCurrentProject,
    });

    render(
      <BrowserRouter>
        <SpaceDashboard />
      </BrowserRouter>
    );

    fireEvent.click(screen.getByText('Project 1'));
    expect(mockSetCurrentProject).toHaveBeenCalledWith(mockProject);
    expect(mockNavigate).toHaveBeenCalledWith('/space/123/project/p1');
  });

  it('should open create project modal', () => {
    render(
      <BrowserRouter>
        <SpaceDashboard />
      </BrowserRouter>
    );

    fireEvent.click(screen.getByText('新建项目'));
    expect(screen.getByTestId('create-project-modal')).toBeInTheDocument();
  });
});
