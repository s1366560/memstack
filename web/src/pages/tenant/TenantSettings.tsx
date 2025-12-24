import React, { useState, useEffect } from 'react'
import { useTenantStore } from '../../stores/tenant'
import { tenantAPI } from '../../services/api'

export const TenantSettings: React.FC = () => {
    const { currentTenant, listTenants } = useTenantStore()
    const [isLoading, setIsLoading] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
    
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        plan: ''
    })

    useEffect(() => {
        if (currentTenant) {
            setFormData({
                name: currentTenant.name,
                description: currentTenant.description || '',
                plan: currentTenant.plan
            })
        }
    }, [currentTenant])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!currentTenant) return

        setIsLoading(true)
        setMessage(null)
        try {
            await tenantAPI.update(currentTenant.id, formData)
            await listTenants() // Refresh store
            setMessage({ type: 'success', text: 'Organization settings updated successfully.' })
        } catch (error) {
            console.error('Failed to update tenant:', error)
            setMessage({ type: 'error', text: 'Failed to update settings. Please try again.' })
        } finally {
            setIsLoading(false)
        }
    }

    if (!currentTenant) return <div className="p-8 text-center text-slate-500">Loading settings...</div>

    return (
        <div className="max-w-4xl mx-auto flex flex-col gap-8 pb-10">
            {/* Header */}
            <div className="flex flex-col gap-1">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Organization Settings</h1>
                <p className="text-slate-500 dark:text-slate-400">Manage your workspace preferences and billing details.</p>
            </div>

            {message && (
                <div className={`px-4 py-3 rounded-lg flex items-center gap-2 text-sm ${
                    message.type === 'success' 
                        ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800'
                        : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                }`}>
                    <span className="material-symbols-outlined text-lg">
                        {message.type === 'success' ? 'check_circle' : 'error'}
                    </span>
                    {message.text}
                </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-8">
                {/* General Settings */}
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg">
                            <span className="material-symbols-outlined">tune</span>
                        </div>
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white">General Information</h2>
                    </div>
                    
                    <div className="grid grid-cols-1 gap-6 max-w-2xl">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                Organization Name
                            </label>
                            <input 
                                type="text" 
                                required
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-2.5 text-slate-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                Description
                            </label>
                            <textarea 
                                rows={3}
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-2.5 text-slate-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all resize-none"
                            />
                        </div>
                    </div>
                </div>

                {/* Plan & Usage */}
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-lg">
                            <span className="material-symbols-outlined">diamond</span>
                        </div>
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Plan & Usage</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-4">Current Plan</p>
                            <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                                <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                    <span className="material-symbols-outlined text-2xl">rocket_launch</span>
                                </div>
                                <div>
                                    <p className="font-bold text-slate-900 dark:text-white capitalize">{currentTenant.plan} Plan</p>
                                    <p className="text-xs text-slate-500">Active since {new Date(currentTenant.created_at).toLocaleDateString()}</p>
                                </div>
                                <button type="button" className="ml-auto text-primary text-sm font-medium hover:underline">Change</button>
                            </div>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-4">Resource Limits</p>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-slate-500">Projects</span>
                                        <span className="font-medium text-slate-900 dark:text-white">3 / {currentTenant.max_projects}</span>
                                    </div>
                                    <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5">
                                        <div className="bg-primary h-1.5 rounded-full" style={{ width: `${(3 / currentTenant.max_projects) * 100}%` }}></div>
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-slate-500">Storage</span>
                                        <span className="font-medium text-slate-900 dark:text-white">1.2GB / {currentTenant.max_storage}GB</span>
                                    </div>
                                    <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5">
                                        <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: '15%' }}></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Danger Zone */}
                <div className="bg-surface-light dark:bg-surface-dark border border-red-200 dark:border-red-900/30 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
                            <span className="material-symbols-outlined">warning</span>
                        </div>
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Danger Zone</h2>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg border border-red-100 dark:border-red-900/30 bg-red-50/50 dark:bg-red-900/10">
                        <div>
                            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Delete Organization</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Permanently delete this organization and all its data. This action cannot be undone.
                            </p>
                        </div>
                        <button 
                            type="button" 
                            className="px-4 py-2 bg-white dark:bg-surface-dark border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm font-medium rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        >
                            Delete Organization
                        </button>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="flex items-center justify-end pt-6 border-t border-slate-200 dark:border-slate-800">
                    <button 
                        type="submit" 
                        disabled={isLoading}
                        className="px-6 py-2.5 rounded-lg bg-primary text-white font-medium hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isLoading && <span className="material-symbols-outlined animate-spin text-sm">progress_activity</span>}
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    )
}
