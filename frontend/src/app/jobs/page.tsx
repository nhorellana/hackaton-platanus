'use client'

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import type { ReactElement } from "react";
import ReactMarkdown from 'react-markdown';

type JobType = 'slack' | 'data' | 'research' | 'mail' | 'market_research' | 'external_research';
type JobStatus = 'CREATED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'pending' | 'in_progress' | 'completed' | 'failed';

interface Job {
    id: string;
    job_id?: string;
    session_id: string;
    job_type: JobType;
    type?: JobType;
    status: JobStatus;
    instructions?: string;
    context_summary?: string;
    created_at?: string;
    updated_at?: string;
    result?: string | {
        content: string;
        sources?: Array<{
            title: string;
            url: string;
            description: string;
        }>;
    };
}

export default function Jobs() {
    const router = useRouter();

    const [jobs, setJobs] = useState<Job[]>([]);
    const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());

    const [sessionId] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('conversation-session-id');
    });

    const [isLoading, setIsLoading] = useState(true);
    const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

    const toggleJobExpanded = (jobId: string) => {
        setExpandedJobs(prev => {
            const newSet = new Set(prev);
            if (newSet.has(jobId)) {
                newSet.delete(jobId);
            } else {
                newSet.add(jobId);
            }
            return newSet;
        });
    };

    const categorizeJobs = () => {
        return {
            market: jobs.filter(j => j.job_type === 'research' || j.job_type === 'market_research' || j.job_type === 'data'),
            internal: jobs.filter(j => j.job_type === 'slack'),
            external: jobs.filter(j => j.job_type === 'external_research' || j.job_type === 'mail')
        };
    };

    useEffect(() => {
        if (!sessionId) return;

        const pollJobs = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs?session_id=${sessionId}`);
                if (response.ok) {
                    const updatedJobs = await response.json();
                    setJobs(updatedJobs);
                    setIsLoading(false);
                    localStorage.setItem('current-jobs', JSON.stringify(updatedJobs));
                }
            } catch (error) {
                console.error('Error polling job status:', error);
                setIsLoading(false);
            }
        };

        pollJobs();

        const interval = setInterval(pollJobs, 10000);

        return () => clearInterval(interval);
    }, [sessionId]);

    const getServiceConfig = (type: JobType) => {
        const configs: Record<JobType, { name: string; description: string; icon: ReactElement; color: string }> = {
            slack: {
                name: 'Slack',
                description: 'Consultar equipo',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14.5 10c-.83 0-1.5-.67-1.5-1.5v-5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5z"/>
                        <path d="M20.5 10H19V8.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                        <path d="M9.5 14c.83 0 1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5S8 21.33 8 20.5v-5c0-.83.67-1.5 1.5-1.5z"/>
                        <path d="M3.5 14H5v1.5c0 .83-.67 1.5-1.5 1.5S2 16.33 2 15.5 2.67 14 3.5 14z"/>
                        <path d="M14 14.5c0-.83.67-1.5 1.5-1.5h5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-5c-.83 0-1.5-.67-1.5-1.5z"/>
                        <path d="M15.5 19H14v1.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"/>
                        <path d="M10 9.5C10 8.67 9.33 8 8.5 8h-5C2.67 8 2 8.67 2 9.5S2.67 11 3.5 11h5c.83 0 1.5-.67 1.5-1.5z"/>
                        <path d="M8.5 5H10V3.5C10 2.67 9.33 2 8.5 2S7 2.67 7 3.5 7.67 5 8.5 5z"/>
                    </svg>
                ),
                color: 'from-pink-500/20 to-purple-500/20 border-pink-500/50 text-pink-400'
            },
            data: {
                name: 'Datos Internos',
                description: 'Historial & Logs',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2c-4 0-8 .5-8 4v12c0 3.5 4 4 8 4s8-.5 8-4V6c0-3.5-4-4-8-4z"/>
                        <path d="M20 12c0 3.5-4 4-8 4s-8-.5-8-4"/>
                        <path d="M20 6c0 3.5-4 4-8 4s-8-.5-8-4"/>
                    </svg>
                ),
                color: 'from-blue-500/20 to-blue-600/20 border-blue-500/50 text-blue-400'
            },
            research: {
                name: 'Deep Research',
                description: 'Web & Papers',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.3-4.3"/>
                    </svg>
                ),
                color: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/50 text-emerald-400'
            },
            mail: {
                name: 'Correo Externo',
                description: 'Contactar expertos',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect width="20" height="16" x="2" y="4" rx="2"/>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                ),
                color: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-400'
            },
            market_research: {
                name: 'Market Research',
                description: 'Análisis de mercado',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.3-4.3"/>
                    </svg>
                ),
                color: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/50 text-emerald-400'
            },
            external_research: {
                name: 'External Research',
                description: 'Investigación externa',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.3-4.3"/>
                    </svg>
                ),
                color: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/50 text-emerald-400'
            }
        };
        return configs[type];
    };

    const getStatusBadge = (status: JobStatus) => {
        const normalizedStatus = status.toLowerCase();
        const badges = {
            created: { text: 'Pendiente', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' },
            pending: { text: 'Pendiente', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' },
            in_progress: { text: 'En Progreso', color: 'bg-blue-500/20 text-blue-400 border-blue-500/50' },
            completed: { text: 'Completado', color: 'bg-green-500/20 text-green-400 border-green-500/50' },
            failed: { text: 'Fallido', color: 'bg-red-500/20 text-red-400 border-red-500/50' }
        };
        return badges[normalizedStatus as keyof typeof badges];
    };

    const parseInstructions = (instructionsStr?: string) => {
        if (!instructionsStr) return null;
        try {
            const parsed = JSON.parse(instructionsStr);
            // If instructions is a string, parse it again
            if (parsed.instructions && typeof parsed.instructions === 'string') {
                try {
                    parsed.instructions = JSON.parse(parsed.instructions);
                } catch {
                    // Keep as string if parsing fails
                }
            }
            return parsed;
        } catch {
            return null;
        }
    };

    const extractJsonFromString = (str: string) => {
        if (!str) return null;
        try {
            // Try to find JSON code block (```json ... ```)
            const jsonBlockMatch = str.match(/```json\s*\n([\s\S]*?)\n```/);
            if (jsonBlockMatch && jsonBlockMatch[1]) {
                return JSON.parse(jsonBlockMatch[1]);
            }
            // Try to parse the string directly as JSON
            return JSON.parse(str);
        } catch {
            return null;
        }
    };

    const handleGenerateSummary = async () => {
        if (!sessionId) return;

        setIsGeneratingSummary(true);

        try {
            // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/summary`, {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json',
            //     },
            //     body: JSON.stringify({ session_id: sessionId }),
            // });

            // if (response.ok) {
            //     const data = await response.json();
            //     localStorage.setItem('summary-text', data.summary || data.text || '');
            //     router.push('/summary');
            // } else {
            //     console.error('Failed to generate summary');
            // }

            router.push('/summary');

        } catch (error) {
            console.error('Error generating summary:', error);
        } finally {
            setIsGeneratingSummary(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col bg-(--color-background)">
            {/* Header */}
            <header className="border-b border-(--color-border) bg-(--color-background) px-6 py-4">
                <div className="mx-auto flex max-w-6xl items-center justify-between">
                    <button
                        onClick={() => router.push('/conversation')}
                        className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text)"
                    >
                        ← Volver a conversación
                    </button>
                    <h1 className="text-lg font-semibold text-(--color-text)">Servicios de Investigación</h1>
                    <button
                        onClick={handleGenerateSummary}
                        disabled={isGeneratingSummary || jobs.length === 0}
                        className="cursor-pointer rounded-md bg-(--color-primary) px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover) disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isGeneratingSummary && (
                            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        )}
                        {isGeneratingSummary ? 'Generando...' : 'Generar Resumen'}
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto px-6 py-8">
                <div className="mx-auto max-w-6xl">
                    {/* Jobs Grid */}
                    <div className="mb-8">
                        {isLoading || jobs.length === 0 ? (
                            <>
                                <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                                    Trabajos en Curso
                                </h2>
                                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-1">
                                    {[1, 2, 3, 4].map((i) => (
                                        <div
                                            key={i}
                                            className="group flex flex-col gap-3 rounded-xl border border-(--color-border) bg-(--color-input-bg) p-5 text-left animate-pulse"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="h-8 w-8 rounded-lg bg-(--color-border)"></div>
                                                <div className="h-5 w-20 rounded bg-(--color-border)"></div>
                                            </div>
                                            <div>
                                                <div className="h-4 w-24 rounded bg-(--color-border)"></div>
                                                <div className="mt-2 h-3 w-32 rounded bg-(--color-border)"></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : (() => {
                            const categorized = categorizeJobs();
                            const renderJobCard = (job: typeof jobs[0]) => {
                                const jobType = job.job_type || job.type;
                                const jobId = job.id || job.job_id;
                                if (!jobType) return null;

                                const config = getServiceConfig(jobType);
                                const statusBadge = getStatusBadge(job.status);
                                const instructions = parseInstructions(job.instructions);
                                const isExpanded = expandedJobs.has(jobId);

                                if (!config || !statusBadge) return null;

                                return (
                                    <div
                                        key={jobId}
                                        className="group flex flex-col gap-3 rounded-xl border border-(--color-border) bg-(--color-input-bg) p-5 text-left"
                                    >
                                        <div
                                            className="flex items-center justify-between cursor-pointer"
                                            onClick={() => toggleJobExpanded(jobId)}
                                        >
                                            <div className="flex items-center gap-3 flex-1">
                                                <div className={`flex h-8 w-8 items-center justify-center rounded-lg border bg-linear-to-br ${config.color}`}>
                                                    {config.icon}
                                                </div>
                                                <div className="flex-1">
                                                    <h3 className="text-sm font-medium text-(--color-text)">{config.name}</h3>
                                                    <p className="mt-0.5 text-xs text-(--color-text-secondary)">{config.description}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className={`rounded border px-2 py-0.5 text-xs font-medium ${statusBadge.color}`}>
                                                    {statusBadge.text}
                                                </span>
                                                <svg
                                                    className={`h-5 w-5 text-(--color-text-secondary) transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                </svg>
                                            </div>
                                        </div>

                                        {isExpanded && (
                                            <div className="pt-3 border-t border-(--color-border)">
                                                {/* Slack - Conversation Panel */}
                                                {jobType === 'slack' && instructions && instructions.contact && (
                                                    <div className="space-y-3">
                                                        {/* Contact Header */}
                                                        <div className="flex items-center gap-3 pb-2 border-b border-(--color-border)">
                                                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-(--color-primary) text-white text-sm font-medium">
                                                                {instructions.contact.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                                                            </div>
                                                            <div>
                                                                <h3 className="text-sm font-medium text-(--color-text)">
                                                                    {instructions.contact.name}
                                                                </h3>
                                                                <p className="text-xs text-(--color-text-secondary)">
                                                                    {instructions.contact.role}
                                                                </p>
                                                            </div>
                                                        </div>

                                                        {/* Conversation */}
                                                        <div className="space-y-2">
                                                            {/* Justification as context message */}
                                                            {instructions.contact.justification && (
                                                                <div className="text-xs text-(--color-text-secondary) bg-(--color-background) rounded-lg p-2 border border-(--color-border)">
                                                                    <div className="font-medium text-(--color-text) mb-1">Contexto</div>
                                                                    {instructions.contact.justification}
                                                                </div>
                                                            )}

                                                            {/* Questions as messages */}
                                                            {instructions.contact.questions && instructions.contact.questions.length > 0 && (
                                                                <div className="space-y-2">
                                                                    <div className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider">
                                                                        Preguntas a realizar ({instructions.contact.questions.length})
                                                                    </div>
                                                                    {instructions.contact.questions.map((question: string, idx: number) => (
                                                                        <div key={idx} className="bg-(--color-background) rounded-lg p-2 border border-(--color-border)">
                                                                            <div className="flex items-start gap-2">
                                                                                <span className="shrink-0 text-[10px] font-medium text-(--color-primary) bg-primary/10 rounded px-1.5 py-0.5">
                                                                                    P{idx + 1}
                                                                                </span>
                                                                                <p className="text-xs text-(--color-text) leading-relaxed flex-1">
                                                                                    {question}
                                                                                </p>
                                                                            </div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Research/Data - Justification and Queries */}
                                                {(jobType === 'research' || jobType === 'data' || jobType === 'market_research' || jobType === 'external_research') && instructions && (
                                                    <div className="space-y-3">
                                                        {/* Objective Section */}
                                                        {(instructions.instructions?.reason || instructions.justification) && (
                                                            <div className="bg-(--color-background) rounded-lg p-3 border border-(--color-border)">
                                                                <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                    Objetivo de la Investigación
                                                                </p>
                                                                <p className="text-xs text-(--color-text) leading-relaxed">
                                                                    {instructions.instructions?.reason || instructions.justification}
                                                                </p>
                                                            </div>
                                                        )}

                                                        {/* Research Findings - Tabs */}
                                                        {instructions.findings && (() => {
                                                            // Parse findings if they're strings with embedded JSON
                                                            const parsedFindings = {
                                                                obstacles: typeof instructions.findings.obstacles === 'string'
                                                                    ? extractJsonFromString(instructions.findings.obstacles)
                                                                    : instructions.findings.obstacles,
                                                                solutions: typeof instructions.findings.solutions === 'string'
                                                                    ? extractJsonFromString(instructions.findings.solutions)
                                                                    : instructions.findings.solutions,
                                                                legal: typeof instructions.findings.legal === 'string'
                                                                    ? extractJsonFromString(instructions.findings.legal)
                                                                    : instructions.findings.legal,
                                                                competitors: typeof instructions.findings.competitors === 'string'
                                                                    ? extractJsonFromString(instructions.findings.competitors)
                                                                    : instructions.findings.competitors,
                                                                market: typeof instructions.findings.market === 'string'
                                                                    ? extractJsonFromString(instructions.findings.market)
                                                                    : instructions.findings.market
                                                            };

                                                            if (!parsedFindings.obstacles && !parsedFindings.solutions && !parsedFindings.legal && !parsedFindings.competitors && !parsedFindings.market) {
                                                                return null;
                                                            }

                                                            return (
                                                            <div className="border border-(--color-border) rounded-lg overflow-hidden">
                                                                {/* Tabs Navigation */}
                                                                <div className="flex border-b border-(--color-border) bg-(--color-background) overflow-x-auto">
                                                                    {parsedFindings.obstacles && (
                                                                        <button className="px-3 py-2 text-xs font-medium text-(--color-text-secondary) hover:text-(--color-text) hover:bg-(--color-input-bg) border-b-2 border-transparent hover:border-(--color-primary) transition-colors whitespace-nowrap">
                                                                            Obstáculos
                                                                        </button>
                                                                    )}
                                                                    {parsedFindings.solutions && (
                                                                        <button className="px-3 py-2 text-xs font-medium text-(--color-text-secondary) hover:text-(--color-text) hover:bg-(--color-input-bg) border-b-2 border-transparent hover:border-(--color-primary) transition-colors whitespace-nowrap">
                                                                            Soluciones
                                                                        </button>
                                                                    )}
                                                                    {parsedFindings.legal && (
                                                                        <button className="px-3 py-2 text-xs font-medium text-(--color-text-secondary) hover:text-(--color-text) hover:bg-(--color-input-bg) border-b-2 border-transparent hover:border-(--color-primary) transition-colors whitespace-nowrap">
                                                                            Legal
                                                                        </button>
                                                                    )}
                                                                    {parsedFindings.competitors && (
                                                                        <button className="px-3 py-2 text-xs font-medium text-(--color-text-secondary) hover:text-(--color-text) hover:bg-(--color-input-bg) border-b-2 border-transparent hover:border-(--color-primary) transition-colors whitespace-nowrap">
                                                                            Competidores
                                                                        </button>
                                                                    )}
                                                                    {parsedFindings.market && (
                                                                        <button className="px-3 py-2 text-xs font-medium text-(--color-text-secondary) hover:text-(--color-text) hover:bg-(--color-input-bg) border-b-2 border-transparent hover:border-(--color-primary) transition-colors whitespace-nowrap">
                                                                            Mercado
                                                                        </button>
                                                                    )}
                                                                </div>

                                                                {/* Tab Content - Show first available */}
                                                                <div className="p-3 bg-(--color-input-bg) max-h-64 overflow-y-auto space-y-4">
                                                                    {/* Obstacles Tab */}
                                                                    {parsedFindings.obstacles && (() => {
                                                                        // Handle different structures: direct array or nested object
                                                                        const technicalObstacles = parsedFindings.obstacles.technical || [];
                                                                        const marketObstacles = parsedFindings.obstacles.market || [];
                                                                        const regulatoryObstacles = parsedFindings.obstacles.regulatory || [];
                                                                        const criticalInsights = parsedFindings.obstacles.critical_insights || [];

                                                                        return (
                                                                            <div className="space-y-3">
                                                                                {technicalObstacles.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Desafíos Técnicos
                                                                                        </p>
                                                                                        <ul className="space-y-1">
                                                                                            {technicalObstacles.slice(0, 5).map((obstacle: string, idx: number) => (
                                                                                                <li key={idx} className="text-xs text-(--color-text) leading-relaxed flex gap-2">
                                                                                                    <span className="text-(--color-primary) shrink-0">•</span>
                                                                                                    <span>{obstacle}</span>
                                                                                                </li>
                                                                                            ))}
                                                                                        </ul>
                                                                                    </div>
                                                                                )}
                                                                                {marketObstacles.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Barreras de Mercado
                                                                                        </p>
                                                                                        <ul className="space-y-1">
                                                                                            {marketObstacles.slice(0, 5).map((obstacle: string, idx: number) => (
                                                                                                <li key={idx} className="text-xs text-(--color-text) leading-relaxed flex gap-2">
                                                                                                    <span className="text-(--color-primary) shrink-0">•</span>
                                                                                                    <span>{obstacle}</span>
                                                                                                </li>
                                                                                            ))}
                                                                                        </ul>
                                                                                    </div>
                                                                                )}
                                                                                {regulatoryObstacles.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Complejidad Regulatoria
                                                                                        </p>
                                                                                        <ul className="space-y-1">
                                                                                            {regulatoryObstacles.slice(0, 5).map((obstacle: string, idx: number) => (
                                                                                                <li key={idx} className="text-xs text-(--color-text) leading-relaxed flex gap-2">
                                                                                                    <span className="text-(--color-primary) shrink-0">•</span>
                                                                                                    <span>{obstacle}</span>
                                                                                                </li>
                                                                                            ))}
                                                                                        </ul>
                                                                                    </div>
                                                                                )}
                                                                                {criticalInsights.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Insights Críticos
                                                                                        </p>
                                                                                        <ul className="space-y-1">
                                                                                            {criticalInsights.slice(0, 5).map((insight: string, idx: number) => (
                                                                                                <li key={idx} className="text-xs text-(--color-text) leading-relaxed flex gap-2">
                                                                                                    <span className="text-(--color-primary) shrink-0">•</span>
                                                                                                    <span>{insight}</span>
                                                                                                </li>
                                                                                            ))}
                                                                                        </ul>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })()}

                                                                    {/* Solutions Tab */}
                                                                    {parsedFindings.solutions && (() => {
                                                                        const manualSolutions = parsedFindings.solutions.manual_solutions || [];
                                                                        const digitalSolutions = parsedFindings.solutions.digital_solutions || [];

                                                                        return (
                                                                            <div className="space-y-3">
                                                                                {manualSolutions.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Soluciones Manuales ({manualSolutions.length})
                                                                                        </p>
                                                                                        <div className="space-y-2">
                                                                                            {manualSolutions.slice(0, 3).map((solution: { name: string; description: string; effectiveness?: string }, idx: number) => (
                                                                                                <div key={idx} className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                                    <p className="text-xs font-medium text-(--color-text)">{solution.name}</p>
                                                                                                    <p className="text-xs text-(--color-text-secondary) mt-1">{solution.description}</p>
                                                                                                    {solution.effectiveness && (
                                                                                                        <p className="text-[10px] text-(--color-primary) mt-1">Efectividad: {solution.effectiveness}</p>
                                                                                                    )}
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                                {digitalSolutions.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Soluciones Digitales ({digitalSolutions.length})
                                                                                        </p>
                                                                                        <div className="space-y-2">
                                                                                            {digitalSolutions.slice(0, 3).map((solution: { name: string; description: string; effectiveness?: string }, idx: number) => (
                                                                                                <div key={idx} className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                                    <p className="text-xs font-medium text-(--color-text)">{solution.name}</p>
                                                                                                    <p className="text-xs text-(--color-text-secondary) mt-1">{solution.description}</p>
                                                                                                    {solution.effectiveness && (
                                                                                                        <p className="text-[10px] text-(--color-primary) mt-1">Efectividad: {solution.effectiveness}</p>
                                                                                                    )}
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })()}

                                                                    {/* Legal Tab */}
                                                                    {parsedFindings.legal && (() => {
                                                                        const industryRegulations = parsedFindings.legal.industry_regulations || [];
                                                                        const criticalInsights = parsedFindings.legal.critical_compliance_insights || [];

                                                                        return (
                                                                            <div className="space-y-3">
                                                                                {industryRegulations.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Regulaciones de Industria ({industryRegulations.length})
                                                                                        </p>
                                                                                        <div className="space-y-2">
                                                                                            {industryRegulations.slice(0, 3).map((reg: { regulation: string; requirements: string; complexity?: string; timeline?: string }, idx: number) => (
                                                                                                <div key={idx} className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                                    <div className="flex items-start justify-between mb-1">
                                                                                                        <p className="text-xs font-medium text-(--color-text) flex-1">{reg.regulation}</p>
                                                                                                        {reg.complexity && (
                                                                                                            <span className="text-[10px] text-(--color-text-secondary) bg-(--color-border) px-1.5 py-0.5 rounded ml-2">
                                                                                                                {reg.complexity}
                                                                                                            </span>
                                                                                                        )}
                                                                                                    </div>
                                                                                                    <p className="text-xs text-(--color-text-secondary)">{reg.requirements}</p>
                                                                                                    {reg.timeline && (
                                                                                                        <p className="text-[10px] text-(--color-primary) mt-1">Timeline: {reg.timeline}</p>
                                                                                                    )}
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                                {criticalInsights.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Cumplimiento Crítico
                                                                                        </p>
                                                                                        <ul className="space-y-1">
                                                                                            {criticalInsights.slice(0, 5).map((insight: string, idx: number) => (
                                                                                                <li key={idx} className="text-xs text-(--color-text) leading-relaxed flex gap-2">
                                                                                                    <span className="text-(--color-primary) shrink-0">•</span>
                                                                                                    <span>{insight}</span>
                                                                                                </li>
                                                                                            ))}
                                                                                        </ul>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })()}

                                                                    {/* Competitors Tab */}
                                                                    {parsedFindings.competitors && (() => {
                                                                        const directCompetitors = parsedFindings.competitors.direct_competitors || [];

                                                                        return (
                                                                            <div className="space-y-2">
                                                                                <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                    Competidores Directos ({directCompetitors.length})
                                                                                </p>
                                                                                <div className="space-y-2">
                                                                                    {directCompetitors.slice(0, 3).map((comp: { name: string; description: string; market_position?: string; strengths?: string[] }, idx: number) => (
                                                                                        <div key={idx} className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                            <div className="flex items-center justify-between mb-1">
                                                                                                <p className="text-xs font-medium text-(--color-text)">{comp.name}</p>
                                                                                                {comp.market_position && (
                                                                                                    <span className="text-[10px] text-(--color-text-secondary) bg-(--color-border) px-1.5 py-0.5 rounded">
                                                                                                        {comp.market_position}
                                                                                                    </span>
                                                                                                )}
                                                                                            </div>
                                                                                            <p className="text-xs text-(--color-text-secondary) mb-1">{comp.description}</p>
                                                                                            {comp.strengths && comp.strengths.length > 0 && (
                                                                                                <div className="mt-2">
                                                                                                    <p className="text-[10px] font-medium text-(--color-text-secondary) mb-1">Fortalezas:</p>
                                                                                                    <ul className="space-y-0.5">
                                                                                                        {comp.strengths.slice(0, 2).map((strength: string, sIdx: number) => (
                                                                                                            <li key={sIdx} className="text-[10px] text-(--color-text) flex gap-1">
                                                                                                                <span className="text-(--color-primary) shrink-0">+</span>
                                                                                                                <span>{strength}</span>
                                                                                                            </li>
                                                                                                        ))}
                                                                                                    </ul>
                                                                                                </div>
                                                                                            )}
                                                                                        </div>
                                                                                    ))}
                                                                                </div>
                                                                            </div>
                                                                        );
                                                                    })()}

                                                                    {/* Market Tab */}
                                                                    {parsedFindings.market && (() => {
                                                                        const marketSize = parsedFindings.market.market_size;
                                                                        const criticalInsights = parsedFindings.market.critical_insights || [];

                                                                        return (
                                                                            <div className="space-y-3">
                                                                                {marketSize && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Tamaño de Mercado
                                                                                        </p>
                                                                                        <div className="grid grid-cols-3 gap-2">
                                                                                            {marketSize.tam && (
                                                                                                <div className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                                    <p className="text-[10px] text-(--color-text-secondary) mb-1">TAM</p>
                                                                                                    <p className="text-sm font-medium text-(--color-text)">
                                                                                                        ${(parseFloat(marketSize.tam.value) / 1000000000).toFixed(1)}B
                                                                                                    </p>
                                                                                                    <p className="text-[10px] text-(--color-text-secondary) mt-1">{marketSize.tam.year}</p>
                                                                                                </div>
                                                                                            )}
                                                                                            {marketSize.sam && (
                                                                                                <div className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                                    <p className="text-[10px] text-(--color-text-secondary) mb-1">SAM</p>
                                                                                                    <p className="text-sm font-medium text-(--color-text)">
                                                                                                        ${(parseFloat(marketSize.sam.value) / 1000000000).toFixed(1)}B
                                                                                                    </p>
                                                                                                    <p className="text-[10px] text-(--color-text-secondary) mt-1">{marketSize.sam.year}</p>
                                                                                                </div>
                                                                                            )}
                                                                                            {marketSize.som && (
                                                                                                <div className="bg-(--color-background) rounded p-2 border border-(--color-border)">
                                                                                                    <p className="text-[10px] text-(--color-text-secondary) mb-1">SOM</p>
                                                                                                    <p className="text-sm font-medium text-(--color-text)">
                                                                                                        ${(parseFloat(marketSize.som.value) / 1000000).toFixed(0)}M
                                                                                                    </p>
                                                                                                    <p className="text-[10px] text-(--color-text-secondary) mt-1">{marketSize.som.year}</p>
                                                                                                </div>
                                                                                            )}
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                                {criticalInsights.length > 0 && (
                                                                                    <div>
                                                                                        <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                                            Insights Clave
                                                                                        </p>
                                                                                        <ul className="space-y-1">
                                                                                            {criticalInsights.slice(0, 3).map((insight: string, idx: number) => (
                                                                                                <li key={idx} className="text-xs text-(--color-text) leading-relaxed flex gap-2">
                                                                                                    <span className="text-(--color-primary) shrink-0">•</span>
                                                                                                    <span>{insight}</span>
                                                                                                </li>
                                                                                            ))}
                                                                                        </ul>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })()}
                                                                </div>
                                                            </div>
                                                            );
                                                        })()}

                                                        {/* Queries Section */}
                                                        {(() => {
                                                            const queries = instructions.instructions?.search_queries || instructions.queries;
                                                            if (!queries || queries.length === 0) return null;

                                                            return (
                                                                <div>
                                                                    <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                        Consultas Realizadas ({queries.length})
                                                                    </p>
                                                                    <div className="space-y-1">
                                                                        {queries.slice(0, 3).map((query: string, idx: number) => (
                                                                            <div key={idx} className="text-xs text-(--color-text-secondary) bg-(--color-background) rounded p-2 border border-(--color-border) leading-relaxed">
                                                                                • {query}
                                                                            </div>
                                                                        ))}
                                                                        {queries.length > 3 && (
                                                                            <p className="text-xs text-(--color-text-secondary) italic mt-1">
                                                                                +{queries.length - 3} consultas más
                                                                            </p>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            );
                                                        })()}
                                                    </div>
                                                )}

                                                {/* Mail - Contact Information */}
                                                {jobType === 'mail' && instructions && instructions.contact && (
                                                    <div>
                                                        <div className="mb-2">
                                                            <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-1">
                                                                Destinatario
                                                            </p>
                                                            <p className="text-xs font-medium text-(--color-text)">
                                                                {instructions.contact.name}
                                                            </p>
                                                            {instructions.contact.email && (
                                                                <p className="text-xs text-(--color-text-secondary)">
                                                                    {instructions.contact.email}
                                                                </p>
                                                            )}
                                                        </div>
                                                        {instructions.contact.justification && (
                                                            <div className="mt-2">
                                                                <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-1">
                                                                    Objetivo
                                                                </p>
                                                                <p className="text-xs text-(--color-text) leading-relaxed">
                                                                    {instructions.contact.justification}
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {/* Results Section - Show if job is completed */}
                                                {job.status.toLowerCase() === 'completed' && job.result && (() => {
                                                    // Parse result if it's a string
                                                    let parsedResult = job.result;
                                                    if (typeof job.result === 'string') {
                                                        try {
                                                            parsedResult = JSON.parse(job.result);
                                                        } catch {
                                                            // If parsing fails, treat as plain string
                                                            parsedResult = { content: job.result };
                                                        }
                                                    }

                                                    // Extract synthesis as the main content for deep research results
                                                    const resultContent = typeof parsedResult === 'string'
                                                        ? parsedResult
                                                        : ((parsedResult as Record<string, unknown>)?.synthesis as string) || ((parsedResult as Record<string, unknown>)?.content as string) || '';

                                                    // Extract findings for sources display
                                                    const resultFindings = typeof parsedResult === 'object' ? (parsedResult as Record<string, unknown>)?.findings as Record<string, string> | undefined : null;

                                                    return (
                                                        <div className="mt-3 pt-3 border-t border-(--color-border)">
                                                            <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider mb-2">
                                                                Resultado
                                                            </p>
                                                            <div className="bg-(--color-background) rounded-lg p-3 border border-(--color-border)">
                                                                <div className="text-xs text-(--color-text) leading-relaxed prose prose-sm prose-invert max-w-none prose-headings:text-(--color-text) prose-p:text-(--color-text) prose-strong:text-(--color-text) prose-ul:text-(--color-text) prose-ol:text-(--color-text)">
                                                                    <ReactMarkdown>{resultContent}</ReactMarkdown>
                                                                </div>

                                                                {/* Findings Sections */}
                                                                {resultFindings && (() => {
                                                                    const findingTypes = ['obstacles', 'solutions', 'legal', 'competitors', 'market'];
                                                                    const availableFindings = findingTypes.filter(type => resultFindings[type]);

                                                                    if (availableFindings.length === 0) return null;

                                                                    return (
                                                                        <div className="mt-4 space-y-3">
                                                                            <p className="text-[10px] font-medium text-(--color-text-secondary) uppercase tracking-wider">
                                                                                Hallazgos Detallados
                                                                            </p>
                                                                            {availableFindings.map((findingType) => {
                                                                                console.log('Finding Data:', findingType, resultFindings[findingType]);
                                                                                const findingData =  <ReactMarkdown>{resultFindings[findingType]}</ReactMarkdown>
                                                                                const labels: Record<string, string> = {
                                                                                    obstacles: 'Obstáculos',
                                                                                    solutions: 'Soluciones',
                                                                                    legal: 'Legal',
                                                                                    competitors: 'Competidores',
                                                                                    market: 'Mercado'
                                                                                };

                                                                                return (
                                                                                    <div key={findingType} className="bg-(--color-input-bg) rounded p-3 border border-(--color-border)">
                                                                                        <p className="text-xs font-medium text-(--color-text) mb-2">
                                                                                            {labels[findingType]}
                                                                                        </p>

                                                                                        {/* Render first item based on type */}
                                                                                        {findingType === 'obstacles' && (
                                                                                            <p className="text-xs text-(--color-text-secondary) leading-relaxed">
                                                                                                {findingData}
                                                                                            </p>
                                                                                        )}

                                                                                        {findingType === 'solutions' && (
                                                                                            <div>
                                                                                                <p className="text-xs font-medium text-(--color-text)">
                                                                                                    {findingData}
                                                                                                </p>
                                                                                            </div>
                                                                                        )}
                                                                                    </div>
                                                                                );
                                                                            })}
                                                                        </div>
                                                                    );
                                                                })()}
                                                            </div>
                                                        </div>
                                                    );
                                                })()}
                                            </div>
                                        )}
                                    </div>
                                );
                            };

                            return (
                                <>
                                    {/* Market Research Section */}
                                    {categorized.market.length > 0 && (
                                        <div className="mb-8">
                                            <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                                                Investigación de mercado
                                            </h2>
                                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-1">
                                                {categorized.market.map(renderJobCard)}
                                            </div>
                                        </div>
                                    )}

                                    {/* Internal Research Section */}
                                    {categorized.internal.length > 0 && (
                                        <div className="mb-8">
                                            <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                                                Investigación interna
                                            </h2>
                                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-1">
                                                {categorized.internal.map(renderJobCard)}
                                            </div>
                                        </div>
                                    )}

                                    {/* External Research Section */}
                                    {categorized.external.length > 0 && (
                                        <div className="mb-8">
                                            <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                                                Investigación externa
                                            </h2>
                                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-1">
                                                {categorized.external.map(renderJobCard)}
                                            </div>
                                        </div>
                                    )}
                                </>
                            );
                        })()}
                    </div>
                </div>
            </div>
        </div>
    );
}
