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
} from 'lucide-react'
import { TaskList } from '../../components/tasks/TaskList'

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

export const TaskDashboard: React.FC = () => {
    const [stats, setStats] = useState<TaskStats | null>(null)
    const [queueDepth, setQueueDepth] = useState<QueueDepth | null>(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    // Chart Data State
    const [queueHistory, setQueueHistory] = useState<{ time: string; count: number }[]>([])

    const fetchData = useCallback(async () => {
        try {
            const [statsData, queueData] = await Promise.all([
                taskAPI.getStats(),
                taskAPI.getQueueDepth(),
            ])

            setStats(statsData)
            setQueueDepth(queueData)

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

            {/* Reusable Task List */}
            <TaskList />
        </div>
    )
}
