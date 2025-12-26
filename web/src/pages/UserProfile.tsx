import React, { useEffect, useState } from 'react'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../services/api'
import { UserUpdate } from '../types/memory'

export const UserProfile: React.FC = () => {
    const { user, setUser } = useAuthStore()
    const [isLoading, setIsLoading] = useState(false)
    const [showSuccess, setShowSuccess] = useState(false)
    const [formData, setFormData] = useState<UserUpdate & { email: string }>({
        name: '',
        email: '',
        profile: {
            job_title: '',
            department: 'Engineering',
            bio: '',
            phone: '',
            location: '',
            language: 'English (US)',
            timezone: 'Pacific Time (US & Canada)',
            avatar_url: ''
        }
    })

    useEffect(() => {
        if (user) {
            setFormData({
                name: user.name,
                email: user.email,
                profile: {
                    job_title: user.profile?.job_title || '',
                    department: user.profile?.department || 'Engineering',
                    bio: user.profile?.bio || '',
                    phone: user.profile?.phone || '',
                    location: user.profile?.location || '',
                    language: user.profile?.language || 'English (US)',
                    timezone: user.profile?.timezone || 'Pacific Time (US & Canada)',
                    avatar_url: user.profile?.avatar_url || ''
                }
            })
        }
    }, [user])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target
        if (name === 'name' || name === 'email') {
            setFormData(prev => ({ ...prev, [name]: value }))
        } else {
            setFormData(prev => ({
                ...prev,
                profile: {
                    ...prev.profile!,
                    [name]: value
                }
            }))
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        try {
            const updateData: UserUpdate = {
                name: formData.name,
                profile: formData.profile
            }
            const updatedUser = await authAPI.updateProfile(updateData)
            setUser(updatedUser)
            setShowSuccess(true)
            setTimeout(() => setShowSuccess(false), 3000)
        } catch (error) {
            console.error('Failed to update profile:', error)
        } finally {
            setIsLoading(false)
        }
    }

    if (!user) return <div className="p-8 text-center">Loading...</div>

    return (
        <div className="mx-auto w-full max-w-7xl p-6 lg:p-8">
            {/* Page Heading */}
            <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Personal Profile</h1>
                    <p className="mt-2 text-slate-500 dark:text-slate-400">Manage your account settings and preferences.</p>
                </div>
                <div className="hidden sm:block">
                    <span className="inline-flex items-center rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20 dark:bg-green-900/30 dark:text-green-400">
                        <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-green-600"></span>
                        Account Active
                    </span>
                </div>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 xl:gap-8">
                {/* Left Column: Summary Card */}
                <div className="lg:col-span-1">
                    <div className="sticky top-24 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-surface-dark">
                        <div className="relative h-32 bg-gradient-to-r from-primary/80 to-blue-600/80"></div>
                        <div className="relative flex flex-col items-center px-6 pb-8">
                            <div className="relative -mt-16 mb-4">
                                <div className="h-32 w-32 overflow-hidden rounded-full border-4 border-white bg-white shadow-md dark:border-surface-dark">
                                    <img
                                        alt={user.name}
                                        className="h-full w-full object-cover"
                                        src={formData.profile?.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=random`}
                                    />
                                </div>
                                <button className="absolute bottom-1 right-1 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-primary text-white shadow-lg transition-transform hover:scale-110 hover:bg-primary-dark">
                                    <span className="material-symbols-outlined text-sm">photo_camera</span>
                                </button>
                            </div>
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{user.name}</h2>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{formData.profile?.job_title || 'No Job Title'}</p>
                            <div className="mt-4 flex w-full flex-col gap-2 border-t border-slate-200 py-4 dark:border-slate-700">
                                <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                                    <span className="material-symbols-outlined text-lg">business</span>
                                    <span>{formData.profile?.department || 'No Department'}</span>
                                </div>
                                <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                                    <span className="material-symbols-outlined text-lg">location_on</span>
                                    <span>{formData.profile?.location || 'No Location'}</span>
                                </div>
                                <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                                    <span className="material-symbols-outlined text-lg">calendar_month</span>
                                    <span>Member since {new Date(user.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                            <div className="mt-2 w-full">
                                <div className="mb-2 flex items-center justify-between text-xs">
                                    <span className="text-slate-500 dark:text-slate-400">Profile Completion</span>
                                    <span className="font-medium text-primary dark:text-blue-400">85%</span>
                                </div>
                                <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
                                    <div className="h-full w-[85%] rounded-full bg-primary"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Settings Form */}
                <div className="lg:col-span-2">
                    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-surface-dark">
                        {/* Tabs */}
                        <div className="border-b border-slate-200 px-6 dark:border-slate-700">
                            <nav aria-label="Tabs" className="-mb-px flex space-x-8">
                                <button aria-current="page" className="border-b-2 border-primary px-1 py-4 text-sm font-medium text-primary dark:text-white">Basic Info</button>
                                <button className="border-b-2 border-transparent px-1 py-4 text-sm font-medium text-slate-500 hover:border-gray-300 hover:text-slate-700 dark:text-slate-400 dark:hover:border-gray-600 dark:hover:text-white">Contact Details</button>
                                <button className="border-b-2 border-transparent px-1 py-4 text-sm font-medium text-slate-500 hover:border-gray-300 hover:text-slate-700 dark:text-slate-400 dark:hover:border-gray-600 dark:hover:text-white">Preferences</button>
                                <button className="border-b-2 border-transparent px-1 py-4 text-sm font-medium text-slate-500 hover:border-gray-300 hover:text-slate-700 dark:text-slate-400 dark:hover:border-gray-600 dark:hover:text-white">Security</button>
                            </nav>
                        </div>
                        <div className="p-6">
                            <form onSubmit={handleSubmit}>
                                {/* Basic Information Section */}
                                <div className="mb-8">
                                    <h3 className="mb-4 text-base font-semibold text-slate-900 dark:text-white">Basic Information</h3>
                                    <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-6">
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="email">Email</label>
                                            <div className="mt-2">
                                                <input className="block w-full rounded-md border-0 py-1.5 text-slate-500 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 bg-gray-50 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-gray-800 dark:ring-gray-700 dark:text-gray-400 sm:text-sm sm:leading-6 cursor-not-allowed" disabled id="email" name="email" type="text" value={formData.email} />
                                            </div>
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="name">Full Name</label>
                                            <div className="mt-2">
                                                <input
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="name"
                                                    name="name"
                                                    type="text"
                                                    value={formData.name}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="job_title">Job Title</label>
                                            <div className="mt-2">
                                                <input
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="job_title"
                                                    name="job_title"
                                                    type="text"
                                                    value={formData.profile?.job_title}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="department">Department</label>
                                            <div className="mt-2">
                                                <select
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="department"
                                                    name="department"
                                                    value={formData.profile?.department}
                                                    onChange={handleChange}
                                                >
                                                    <option>Engineering</option>
                                                    <option>Product</option>
                                                    <option>Design</option>
                                                    <option>Marketing</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="col-span-full">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="bio">About</label>
                                            <div className="mt-2">
                                                <textarea
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="bio"
                                                    name="bio"
                                                    rows={3}
                                                    value={formData.profile?.bio}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Brief description for your profile. Max 200 characters.</p>
                                        </div>
                                    </div>
                                </div>
                                <hr className="border-slate-200 dark:border-slate-700 my-8" />
                                {/* Contact Information Section */}
                                <div className="mb-8">
                                    <h3 className="mb-4 text-base font-semibold text-slate-900 dark:text-white">Contact Information</h3>
                                    <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-6">
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="phone">Phone Number</label>
                                            <div className="mt-2">
                                                <input
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="phone"
                                                    name="phone"
                                                    type="tel"
                                                    value={formData.profile?.phone}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="location">Office Location</label>
                                            <div className="mt-2">
                                                <div className="relative rounded-md shadow-sm">
                                                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                                        <span className="material-symbols-outlined text-gray-400 text-lg">location_on</span>
                                                    </div>
                                                    <input
                                                        className="block w-full rounded-md border-0 py-1.5 pl-10 text-slate-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                        id="location"
                                                        name="location"
                                                        placeholder="City, Country"
                                                        type="text"
                                                        value={formData.profile?.location}
                                                        onChange={handleChange}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <hr className="border-slate-200 dark:border-slate-700 my-8" />
                                {/* Preferences Section */}
                                <div className="mb-8">
                                    <h3 className="mb-4 text-base font-semibold text-slate-900 dark:text-white">System Preferences</h3>
                                    <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-6">
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="language">Language</label>
                                            <div className="mt-2">
                                                <select
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="language"
                                                    name="language"
                                                    value={formData.profile?.language}
                                                    onChange={handleChange}
                                                >
                                                    <option>English (US)</option>
                                                    <option>Chinese (Simplified)</option>
                                                    <option>Japanese</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label className="block text-sm font-medium leading-6 text-slate-900 dark:text-white" htmlFor="timezone">Timezone</label>
                                            <div className="mt-2">
                                                <select
                                                    className="block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-background-dark dark:ring-gray-700 dark:text-white sm:text-sm sm:leading-6"
                                                    id="timezone"
                                                    name="timezone"
                                                    value={formData.profile?.timezone}
                                                    onChange={handleChange}
                                                >
                                                    <option>Pacific Time (US & Canada)</option>
                                                    <option>Eastern Time (US & Canada)</option>
                                                    <option>London (UTC)</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex items-center justify-end gap-x-4 border-t border-slate-200 pt-6 dark:border-slate-700">
                                    <button className="rounded-md px-3 py-2 text-sm font-semibold text-slate-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 dark:ring-gray-600 dark:text-white dark:hover:bg-gray-800" type="button">Cancel</button>
                                    <button
                                        className="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
                                        type="submit"
                                        disabled={isLoading}
                                    >
                                        {isLoading ? 'Saving...' : 'Save Changes'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            {/* Toast Notification */}
            {showSuccess && (
                <div className="pointer-events-none fixed inset-0 flex items-end px-4 py-6 sm:items-start sm:p-6 z-50">
                    <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
                        <div className="pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 dark:bg-surface-dark dark:ring-white dark:ring-opacity-10 transform transition-all duration-300 ease-out translate-y-0 opacity-100">
                            <div className="p-4">
                                <div className="flex items-start">
                                    <div className="flex-shrink-0">
                                        <span className="material-symbols-outlined text-green-400">check_circle</span>
                                    </div>
                                    <div className="ml-3 w-0 flex-1 pt-0.5">
                                        <p className="text-sm font-medium text-slate-900 dark:text-white">Successfully saved!</p>
                                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Your profile information has been updated.</p>
                                    </div>
                                    <div className="ml-4 flex flex-shrink-0">
                                        <button
                                            className="inline-flex rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:bg-surface-dark dark:hover:text-gray-300"
                                            onClick={() => setShowSuccess(false)}
                                        >
                                            <span className="sr-only">Close</span>
                                            <span className="material-symbols-outlined text-sm">close</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
