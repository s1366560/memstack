import { Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme, App as AntdApp } from 'antd'
import { Login } from './pages/Login'
import { SpaceListPage } from './pages/SpaceListPage'
import { SpaceDashboard } from './pages/SpaceDashboard'
import { ProjectDashboard } from './pages/ProjectDashboard'
import { useAuthStore } from './stores/auth'
import './App.css'

function App() {
    const { isAuthenticated } = useAuthStore()

    return (
        <ConfigProvider
            theme={{
                algorithm: theme.defaultAlgorithm,
                token: {
                    colorPrimary: '#1890ff',
                },
            }}
        >
            <AntdApp>
                <Routes>
                    <Route
                        path="/login"
                        element={!isAuthenticated ? <Login /> : <Navigate to="/" replace />}
                    />

                    {/* Protected Routes */}
                    <Route
                        path="/"
                        element={isAuthenticated ? <Navigate to="/spaces" replace /> : <Navigate to="/login" replace />}
                    />
                    <Route
                        path="/spaces"
                        element={isAuthenticated ? <SpaceListPage /> : <Navigate to="/login" replace />}
                    />
                    <Route
                        path="/space/:spaceId"
                        element={isAuthenticated ? <SpaceDashboard /> : <Navigate to="/login" replace />}
                    />
                    <Route
                        path="/space/:spaceId/project/:projectId"
                        element={isAuthenticated ? <ProjectDashboard /> : <Navigate to="/login" replace />}
                    />

                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AntdApp>
        </ConfigProvider>
    )
}

export default App