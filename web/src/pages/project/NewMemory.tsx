import React, { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'
import { memoryAPI } from '../../services/api'

export const NewMemory: React.FC = () => {
    const { projectId } = useParams()
    const navigate = useNavigate()
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)
    const [title, setTitle] = useState('')
    const [content, setContent] = useState('')
    const [tags, setTags] = useState<string[]>(['meeting', 'strategy'])
    const [newTag, setNewTag] = useState('')
    const [isSaving, setIsSaving] = useState(false)
    const [isOptimizing, setIsOptimizing] = useState(false)

    const handleAddTag = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && newTag.trim()) {
            setTags([...tags, newTag.trim()])
            setNewTag('')
        }
    }

    const removeTag = (tagToRemove: string) => {
        setTags(tags.filter(tag => tag !== tagToRemove))
    }

    const insertMarkdown = (prefix: string, suffix: string = '') => {
        const textarea = textareaRef.current
        if (!textarea) return

        const start = textarea.selectionStart
        const end = textarea.selectionEnd
        const text = content
        const before = text.substring(0, start)
        const selection = text.substring(start, end)
        const after = text.substring(end)

        const newText = before + prefix + selection + suffix + after
        setContent(newText)

        setTimeout(() => {
            textarea.focus()
            textarea.setSelectionRange(start + prefix.length, end + prefix.length)
        }, 0)
    }

    const handleAIAssist = async () => {
        if (!content) return
        setIsOptimizing(true)
        try {
            const result = await graphitiService.optimizeContent({ content })
            setContent(result.content)
        } catch (error) {
            console.error('Failed to optimize content:', error)
        } finally {
            setIsOptimizing(false)
        }
    }

    const handleSave = async () => {
        if (!projectId || !content) return

        setIsSaving(true)
        try {
            await memoryAPI.create(projectId, {
                title,
                content,
                project_id: projectId,
                tags,
                content_type: 'text',
                metadata: {
                    tags: tags,
                    source: 'web_console'
                }
            })
            navigate(`/project/${projectId}/memories`)
        } catch (error) {
            console.error('Failed to create memory:', error)
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] -m-6 lg:-m-10">
            {/* Top Header / Breadcrumbs - Integrated into page since layout handles main header */}
            <div className="flex shrink-0 items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark px-6 py-3">
                <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    <Link to={`/project/${projectId}/memories`} className="hover:text-primary transition-colors">Memories</Link>
                    <span>/</span>
                    <span className="font-medium text-slate-900 dark:text-white">New Memory</span>
                </div>
                <div className="flex gap-3">
                    <button className="rounded-lg border border-slate-300 dark:border-slate-600 bg-transparent px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        Save as Draft
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving || !content}
                        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary/90 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {isSaving ? (
                            <span className="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
                        ) : (
                            <span className="material-symbols-outlined text-[20px]">save</span>
                        )}
                        Save Memory
                    </button>
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto bg-background-light dark:bg-background-dark p-6 lg:p-8">
                <div className="mx-auto max-w-6xl flex flex-col gap-6">
                    {/* Page Heading */}
                    <div>
                        <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">New Memory Entry</h1>
                        <p className="mt-1 text-slate-500 dark:text-slate-400">Create and format your intelligent memory with AI assistance.</p>
                    </div>

                    {/* Main Entry Card */}
                    <div className="flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark shadow-sm overflow-hidden">
                        {/* Metadata Inputs */}
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 border-b border-slate-100 dark:border-slate-800">
                            {/* Title */}
                            <div className="md:col-span-8">
                                <label className="mb-2 block text-sm font-medium text-slate-900 dark:text-white">Title <span className="text-slate-400 font-normal">(Optional)</span></label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-2.5 text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                    placeholder="e.g. Q3 Strategy Meeting Notes"
                                />
                            </div>
                            {/* Context */}
                            <div className="md:col-span-4">
                                <label className="mb-2 block text-sm font-medium text-slate-900 dark:text-white">Project Context</label>
                                <div className="relative">
                                    <select className="w-full appearance-none rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-2.5 text-slate-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                                        <option>Project Alpha</option>
                                        <option>Marketing Q3</option>
                                        <option>Engineering</option>
                                    </select>
                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                                        <span className="material-symbols-outlined text-[20px]">expand_more</span>
                                    </div>
                                </div>
                            </div>
                            {/* Tags */}
                            <div className="md:col-span-12">
                                <label className="mb-2 block text-sm font-medium text-slate-900 dark:text-white">Tags</label>
                                <div className="flex flex-wrap gap-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-2 min-h-[46px]">
                                    {tags.map(tag => (
                                        <span key={tag} className="flex items-center gap-1 rounded bg-slate-200 dark:bg-slate-700 px-2 py-1 text-sm font-medium text-slate-800 dark:text-slate-200">
                                            #{tag}
                                            <button onClick={() => removeTag(tag)} className="ml-1 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
                                                <span className="material-symbols-outlined text-[14px]">close</span>
                                            </button>
                                        </span>
                                    ))}
                                    <input
                                        type="text"
                                        value={newTag}
                                        onChange={(e) => setNewTag(e.target.value)}
                                        onKeyDown={handleAddTag}
                                        className="bg-transparent text-sm outline-none placeholder:text-slate-500 text-slate-900 dark:text-white min-w-[100px]"
                                        placeholder="+ Add tag..."
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Editor Toolbar */}
                        <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#1a1d26] px-4 py-2">
                            <div className="flex items-center gap-1">
                                <div className="flex items-center rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1 shadow-sm">
                                    <button onClick={() => insertMarkdown('**', '**')} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary dark:text-slate-400 dark:hover:bg-slate-700 transition-colors" title="Bold">
                                        <span className="material-symbols-outlined text-[20px]">format_bold</span>
                                    </button>
                                    <button onClick={() => insertMarkdown('*', '*')} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary dark:text-slate-400 dark:hover:bg-slate-700 transition-colors" title="Italic">
                                        <span className="material-symbols-outlined text-[20px]">format_italic</span>
                                    </button>
                                    <button onClick={() => insertMarkdown('### ')} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary dark:text-slate-400 dark:hover:bg-slate-700 transition-colors" title="Heading">
                                        <span className="material-symbols-outlined text-[20px]">title</span>
                                    </button>
                                </div>
                                <div className="w-px h-6 bg-slate-300 dark:bg-slate-700 mx-2"></div>
                                <div className="flex items-center rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1 shadow-sm">
                                    <button onClick={() => insertMarkdown('- ')} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary dark:text-slate-400 dark:hover:bg-slate-700 transition-colors" title="List">
                                        <span className="material-symbols-outlined text-[20px]">format_list_bulleted</span>
                                    </button>
                                    <button onClick={() => insertMarkdown('[', '](url)')} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary dark:text-slate-400 dark:hover:bg-slate-700 transition-colors" title="Link">
                                        <span className="material-symbols-outlined text-[20px]">link</span>
                                    </button>
                                    <button onClick={() => insertMarkdown('```\n', '\n```')} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary dark:text-slate-400 dark:hover:bg-slate-700 transition-colors" title="Code Block">
                                        <span className="material-symbols-outlined text-[20px]">code</span>
                                    </button>
                                </div>
                            </div>
                            {/* AI Features */}
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={handleAIAssist}
                                    disabled={isOptimizing || !content}
                                    className="flex items-center gap-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 px-3 py-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors border border-indigo-100 dark:border-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isOptimizing ? (
                                        <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                                    ) : (
                                        <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
                                    )}
                                    {isOptimizing ? 'Optimizing...' : 'AI Assist'}
                                </button>
                                <div className="flex rounded-lg border border-slate-200 dark:border-slate-700 p-0.5 bg-slate-100 dark:bg-slate-800">
                                    <button className="rounded px-3 py-1 text-xs font-medium bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white">Split</button>
                                    <button className="rounded px-3 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">Edit</button>
                                    <button className="rounded px-3 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">Preview</button>
                                </div>
                            </div>
                        </div>

                        {/* Editor Content Area */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 h-[600px] divide-y lg:divide-y-0 lg:divide-x divide-slate-200 dark:divide-slate-800">
                            {/* Left: Markdown Input */}
                            <div className="flex flex-col h-full bg-white dark:bg-surface-dark relative">
                                <textarea
                                    ref={textareaRef}
                                    className="w-full h-full resize-none border-none p-6 outline-none text-slate-800 dark:text-slate-200 font-mono text-sm leading-relaxed bg-transparent focus:ring-0"
                                    placeholder="# Start typing your memory here...


You can use Markdown syntax to format your text.

- Use lists to organize thoughts
- **Bold** key concepts
- Connect ideas with links"
                                    value={content}
                                    onChange={(e) => setContent(e.target.value)}
                                ></textarea>
                                <div className="absolute bottom-4 right-4 text-xs text-slate-400 pointer-events-none">Markdown Supported</div>
                            </div>
                            {/* Right: Preview */}
                            <div className="flex flex-col h-full bg-slate-50/50 dark:bg-[#1a1d26]/50 p-6 overflow-y-auto">
                                <div className="prose prose-sm dark:prose-invert max-w-none">
                                    {content ? (
                                        <div className="whitespace-pre-wrap">{content}</div>
                                    ) : (
                                        <>
                                            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Q3 Strategy Meeting Notes</h1>
                                            <p className="text-slate-600 dark:text-slate-300 mb-4">Initial thoughts on the <a className="text-primary hover:underline" href="#">upcoming quarter</a> and resource allocation.</p>
                                            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mt-6 mb-2">Key Objectives</h3>
                                            <ul className="list-disc pl-5 space-y-1 text-slate-600 dark:text-slate-300 mb-4">
                                                <li>Increase user retention by 15%</li>
                                                <li>Launch the <strong>Beta Feature</strong> set by mid-August</li>
                                                <li>Optimize memory indexing latency</li>
                                            </ul>
                                            <div className="rounded-lg bg-slate-100 dark:bg-slate-800 p-4 border-l-4 border-primary my-4">
                                                <p className="italic text-slate-700 dark:text-slate-300 m-0">"The focus should remain on intelligent retrieval, not just storage."</p>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Footer Status Bar */}
                        <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-surface-dark px-6 py-3 text-xs text-slate-500 dark:text-slate-400">
                            <div className="flex items-center gap-4">
                                <span>Last saved: Just now</span>
                                <span className="flex items-center gap-1">
                                    <span className="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                                    Online
                                </span>
                            </div>
                            <div className="flex items-center gap-4">
                                <span>Word count: {content.split(/\s+/).filter(Boolean).length}</span>
                                <span>Character count: {content.length}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
