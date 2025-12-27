import React, { useEffect, useState, useCallback, useMemo } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { taskAPI } from '../../services/api'
import { format } from 'date-fns'
import {
    RefreshCw,
    Plus,
    ListTodo,
    Gauge,
    Hourglass,
    AlertCircle,
    Search,
    MoreVertical,
    ChevronLeft,
    ChevronRight,
} from 'lucide-react'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
)

interface TaskStats {
    total: number
    pending: number
    processing: number
    completed: number
    failed: number
    throughput_per_minute: number
    error_rate: number
}

interface QueueDepth {
    queues: Record<string, number>
    total: number
}

interface RecentTask {
    id: string
    name: string
    status: string
    created_at: string
    completed_at: string | null
    error: string | null
    worker_id: string | null
    retries: number
    duration: string | null
}

export const TaskDashboard: React.FC = () => {
    const [stats, setStats] = useState<TaskStats | null>(null)
    const [queueDepth, setQueueDepth] = useState<QueueDepth | null>(null)
    const [recentTasks, setRecentTasks] = useState<RecentTask[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    // Filters
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState('All Statuses')

    // Chart Data State
    const [queueHistory, setQueueHistory] = useState<{ time: string; count: number }[]>([])

    const fetchData = useCallback(async () => {
        try {
            const [statsData, queueData, recentData] = await Promise.all([
                taskAPI.getStats(),
                taskAPI.getQueueDepth(),
                taskAPI.getRecentTasks({ limit: 50 }),
            ])

            setStats(statsData)
            setQueueDepth(queueData)
            setRecentTasks(recentData)

            // Update queue history for chart
            setQueueHistory((prev) => {
                const now = new Date()
                const newPoint = {
                    time: format(now, 'HH:mm'),
                    count: queueData.total,
                }
                const newHistory = [...prev, newPoint]
                if (newHistory.length > 20) newHistory.shift() // Keep last 20 points
                return newHistory
            })

            setLoading(false)
            setRefreshing(false)
        } catch (error) {
            console.error('Failed to fetch task dashboard data:', error)
            setLoading(false)
            setRefreshing(false)
        }
    }, [])

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 5000)
        return () => clearInterval(interval)
    }, [fetchData])

    const handleRefresh = () => {
        setRefreshing(true)
        fetchData()
    }

    const handleRetry = async (taskId: string) => {
        try {
            await taskAPI.retryTask(taskId)
            fetchData()
        } catch (error) {
            console.error(`Failed to retry task ${taskId}:`, error)
            alert('Failed to retry task. Please try again.')
        }
    }

    // Filtered tasks
    const filteredTasks = useMemo(() => {
        return recentTasks.filter(task => {
            const matchesSearch = task.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                task.name.toLowerCase().includes(searchQuery.toLowerCase())
            const matchesStatus = statusFilter === 'All Statuses' ||
                task.status.toLowerCase() === statusFilter.toLowerCase()
            return matchesSearch && matchesStatus
        })
    }, [recentTasks, searchQuery, statusFilter])

    // Chart Configurations
    const lineChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                mode: 'index' as const,
                intersect: false,
            },
        },
        scales: {
            x: {
                grid: {
                    display: false,
                },
                ticks: {
                    color: '#64748b',
                    font: {
                        size: 11
                    }
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(226, 232, 240, 0.5)',
                },
                ticks: {
                    color: '#64748b',
                    font: {
                        size: 11
                    }
                }
            },
        },
        elements: {
            line: {
                tension: 0.4,
            },
            point: {
                radius: 0,
                hitRadius: 10,
                hoverRadius: 4,
            }
        },
        interaction: {
            mode: 'nearest' as const,
            axis: 'x' as const,
            intersect: false
        }
    }

    const lineChartData = {
        labels: queueHistory.map((h) => h.time),
        datasets: [
            {
                label: 'Pending Tasks',
                data: queueHistory.map((h) => h.count),
                borderColor: '#2563eb', // primary blue
                backgroundColor: (context: any) => {
                    const ctx = context.chart.ctx;
                    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
                    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.2)');
                    gradient.addColorStop(1, 'rgba(37, 99, 235, 0)');
                    return gradient;
                },
                fill: true,
                borderWidth: 2,
            },
        ],
    }

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
            case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
            case 'processing': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200'
            default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
        }
    }

    const getStatusDot = (status: string) => {
        switch (status.toLowerCase()) {
            case 'completed': return 'bg-green-600'
            case 'failed': return 'bg-red-600'
            case 'processing': return 'bg-blue-600'
            default: return 'bg-gray-500'
        }
    }

    if (loading && !stats) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        )
    }

    return (
        <div className="mx-auto max-w-[1200px] flex flex-col gap-6">
            {/* Page Heading */}
            <div className="flex flex-wrap justify-between items-end gap-4 py-2">
                <div className="flex flex-col gap-1">
                    <h2 className="text-slate-900 dark:text-white tracking-tight text-[32px] font-bold leading-tight">
                        Task Status Dashboard
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-normal leading-normal">
                        Real-time overview of system throughput and queue health.
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 dark:hover:bg-slate-700 flex items-center gap-2 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={`size-5 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    <button className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-blue-700 flex items-center gap-2 transition-colors">
                        <Plus className="size-5" />
                        New Task
                    </button>
                </div>
            </div>

            {/* KPI Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Tasks */}
                <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Total Tasks (All Time)</p>
                        <ListTodo className="text-slate-400 dark:text-slate-500 size-5" />
                    </div>
                    <div className="flex items-end gap-2 mt-2">
                        <p className="text-slate-900 dark:text-white text-2xl font-bold leading-none">
                            {stats?.total.toLocaleString()}
                        </p>
                    </div>
                </div>

                {/* Throughput */}
                <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Throughput</p>
                        <Gauge className="text-slate-400 dark:text-slate-500 size-5" />
                    </div>
                    <div className="flex items-end gap-2 mt-2">
                        <p className="text-slate-900 dark:text-white text-2xl font-bold leading-none">
                            {stats?.throughput_per_minute.toFixed(1)}/min
                        </p>
                    </div>
                </div>

                {/* Pending */}
                <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Pending</p>
                        <Hourglass className="text-slate-400 dark:text-slate-500 size-5" />
                    </div>
                    <div className="flex items-end gap-2 mt-2">
                        <p className="text-slate-900 dark:text-white text-2xl font-bold leading-none">
                            {stats?.pending.toLocaleString()}
                        </p>
                    </div>
                </div>

                {/* Failed */}
                <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <div className="absolute right-0 top-0 h-full w-1 bg-red-500"></div>
                    <div className="flex justify-between items-start">
                        <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Failed</p>
                        <AlertCircle className="text-red-500 size-5" />
                    </div>
                    <div className="flex items-end gap-2 mt-2">
                        <p className="text-slate-900 dark:text-white text-2xl font-bold leading-none">
                            {stats?.failed.toLocaleString()}
                        </p>
                        <span className="text-slate-500 dark:text-slate-400 text-xs font-normal">
                            {stats?.error_rate.toFixed(1)}% Rate
                        </span>
                    </div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Queue Depth Chart */}
                <div className="lg:col-span-2 flex flex-col gap-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
                    <div className="flex justify-between items-center">
                        <div>
                            <p className="text-slate-900 dark:text-white text-lg font-semibold leading-normal">Queue Depth Over Time</p>
                            <p className="text-slate-500 dark:text-slate-400 text-sm font-normal">Tasks waiting for processing • Real-time</p>
                        </div>
                        <div className="text-right">
                            <p className="text-slate-900 dark:text-white text-2xl font-bold">
                                Current: {queueDepth?.total}
                            </p>
                        </div>
                    </div>
                    <div className="w-full h-[200px] mt-2 relative">
                        <Line options={lineChartOptions} data={lineChartData} />
                    </div>
                </div>

                {/* Task Breakdown (Progress Bars) */}
                <div className="flex flex-col gap-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
                    <div>
                        <p className="text-slate-900 dark:text-white text-lg font-semibold leading-normal">Task Status</p>
                        <p className="text-slate-500 dark:text-slate-400 text-sm font-normal">Distribution</p>
                    </div>
                    <div className="flex flex-col justify-center flex-1 gap-5">
                        {[
                            { label: 'Completed', value: stats?.completed || 0, color: 'bg-green-600', total: stats?.total || 1 },
                            { label: 'Processing', value: stats?.processing || 0, color: 'bg-blue-600', total: stats?.total || 1 },
                            { label: 'Failed', value: stats?.failed || 0, color: 'bg-red-500', total: stats?.total || 1 },
                            { label: 'Pending', value: stats?.pending || 0, color: 'bg-yellow-500', total: stats?.total || 1 }
                        ].map((item) => (
                            <div key={item.label} className="space-y-1">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500 dark:text-slate-400 font-medium">{item.label}</span>
                                    <span className="text-slate-900 dark:text-white font-bold">{item.value.toLocaleString()}</span>
                                </div>
                                <div className="h-2 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${item.color} rounded-full transition-all duration-500`}
                                        style={{ width: `${Math.max(2, (item.value / item.total) * 100)}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Tasks Table Container */}
            <div className="flex flex-col rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm overflow-hidden">
                {/* Filter Toolbar */}
                <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-50/50 dark:bg-slate-800">
                    <h3 className="text-slate-900 dark:text-white text-base font-bold whitespace-nowrap">Recent Tasks</h3>
                    <div className="flex flex-wrap gap-3 w-full sm:w-auto">
                        {/* Search */}
                        <div className="relative grow sm:grow-0">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search className="text-slate-400 size-5" />
                            </div>
                            <input
                                className="block w-full sm:w-64 pl-10 pr-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg leading-5 bg-white dark:bg-slate-800 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary sm:text-sm dark:text-white transition-all"
                                placeholder="Search Task ID or Name..."
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        {/* Filters */}
                        <select
                            className="block w-auto pl-3 pr-10 py-2 text-base border-slate-300 dark:border-slate-600 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm rounded-lg bg-white dark:bg-slate-800 dark:text-white"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                        >
                            <option>All Statuses</option>
                            <option>Completed</option>
                            <option>Processing</option>
                            <option>Failed</option>
                            <option>Pending</option>
                        </select>
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                        <thead className="bg-slate-50 dark:bg-slate-800/50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider" scope="col">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider" scope="col">Task ID</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider" scope="col">Type</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider" scope="col">Worker ID</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider" scope="col">Duration</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider" scope="col">Timestamp</th>
                                <th className="relative px-6 py-3" scope="col">
                                    <span className="sr-only">Actions</span>
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                            {filteredTasks.length > 0 ? (
                                filteredTasks.map((task) => (
                                    <tr key={task.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                                                <span className={`size-1.5 rounded-full mr-1.5 ${task.status === 'processing' ? 'animate-pulse' : ''} ${getStatusDot(task.status)}`}></span>
                                                {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-white font-mono">
                                            {task.id.substring(0, 8)}...
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-300">
                                            {task.name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400 font-mono">
                                            {task.worker_id || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                                            {task.duration || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                                            {format(new Date(task.created_at), 'MMM d, HH:mm:ss')}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex items-center justify-end gap-2">
                                                {task.status === 'failed' && (
                                                    <button
                                                        onClick={() => handleRetry(task.id)}
                                                        className="text-primary hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium text-xs mr-2"
                                                    >
                                                        Retry
                                                    </button>
                                                )}
                                                <button className="text-slate-500 hover:text-primary dark:text-slate-400 dark:hover:text-white">
                                                    <MoreVertical className="size-5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                                        <div className="flex flex-col items-center gap-2">
                                            <Search className="size-8 text-slate-300" />
                                            <p>No tasks found matching your filters</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
                {/* Pagination */}
                <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 flex items-center justify-between">
                    <div className="text-sm text-slate-500 dark:text-slate-400">
                        Showing <span className="font-medium text-slate-900 dark:text-white">1</span> to <span className="font-medium text-slate-900 dark:text-white">{Math.min(filteredTasks.length, 50)}</span> of <span className="font-medium text-slate-900 dark:text-white">{stats?.total || 0}</span> results
                    </div>
                    <div className="flex gap-2">
                        <button className="px-3 py-1 border border-slate-200 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-300 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 flex items-center gap-1" disabled>
                            <ChevronLeft className="size-4" /> Previous
                        </button>
                        <button className="px-3 py-1 border border-slate-200 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-300 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 flex items-center gap-1">
                            Next <ChevronRight className="size-4" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
