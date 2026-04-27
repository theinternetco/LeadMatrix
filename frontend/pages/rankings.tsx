'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import styles from '../styles/RankingTracker.module.css';
import API_BASE from '../lib/api';

// ✅ Enterprise Interfaces
interface FormData {
    businessName: string;
    location: string;
    keywords: string[];
    useProxy: boolean;
    proxyIp: string;
    enableNotifications: boolean;
    trackingFrequency: 'hourly' | 'daily' | 'weekly';
}

interface TrackingStatus {
    status: 'started' | 'processing' | 'completed' | 'error';
    progress: number;
    total: number;
    message?: string;
    elapsed_time?: number;
    estimated_time_remaining?: number;
    current_keyword?: string;
    processed_keywords?: string[];
}

interface RankingResult {
    keyword: string;
    position?: number;
    found: boolean;
    timestamp: string;
    url?: string;
    search_engine?: string;
    rank_change?: number;
    visibility_score?: number;
}

interface ResultData {
    summary: {
        total_keywords: number;
        found_count: number;
        success_rate: number;
        execution_time?: number;
        average_position?: number;
        visibility_index?: number;
    };
    results: RankingResult[];
    metadata: {
        tracking_id: string;
        started_at: string;
        completed_at: string;
        device_type: string;
    };
}

interface ApiError {
    detail?: string;
    message?: string;
}

const API_BASE_URL = API_BASE;
const POLL_INTERVAL = 2000;
const MAX_POLL_ATTEMPTS = 300;

export default function RankingTracker() {
    // ✅ State Management
    const [formData, setFormData] = useState<FormData>({
        businessName: '',
        location: '',
        keywords: [],
        useProxy: false,
        proxyIp: '',
        enableNotifications: true,
        trackingFrequency: 'daily'
    });

    const [currentKeyword, setCurrentKeyword] = useState<string>('');
    const [tracking, setTracking] = useState<TrackingStatus | null>(null);
    const [results, setResults] = useState<ResultData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [trackingId, setTrackingId] = useState<string | null>(null);
    const [pollCount, setPollCount] = useState<number>(0);
    const [sortKey, setSortKey] = useState<'position' | 'keyword' | 'timestamp'>('position');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, []);

    // ✅ Sorted Results Computation
    const sortedResults = useMemo(() => {
        if (!results?.results) return [];
        const sorted = [...results.results].sort((a, b) => {
            let compareA, compareB;
            switch (sortKey) {
                case 'position':
                    compareA = a.position || 999;
                    compareB = b.position || 999;
                    break;
                case 'keyword':
                    compareA = a.keyword.toLowerCase();
                    compareB = b.keyword.toLowerCase();
                    break;
                case 'timestamp':
                    compareA = new Date(a.timestamp).getTime();
                    compareB = new Date(b.timestamp).getTime();
                    break;
                default:
                    return 0;
            }
            return sortOrder === 'asc'
                ? compareA > compareB
                    ? 1
                    : -1
                : compareA < compareB
                  ? 1
                  : -1;
        });
        return sorted;
    }, [results?.results, sortKey, sortOrder]);

    // ✅ Statistics
    const stats = useMemo(() => {
        if (!results?.results) return null;
        const topPositions = results.results.filter((r) => r.position && r.position <= 3);
        const firstPageRankings = results.results.filter((r) => r.position && r.position <= 10);
        const avgPosition =
            results.results.filter((r) => r.position).reduce((acc, r) => acc + (r.position || 0), 0) /
                Math.max(results.results.filter((r) => r.position).length, 1) || 0;

        return {
            topThree: topPositions.length,
            firstPage: firstPageRankings.length,
            avgPosition: avgPosition.toFixed(1),
            notRanked: results.results.length - results.summary.found_count
        };
    }, [results?.results, results?.summary.found_count]);

    // ✅ Handlers
    const handleAddKeyword = useCallback((): void => {
        if (currentKeyword.trim() && currentKeyword.length > 0) {
            if (!formData.keywords.includes(currentKeyword.trim())) {
                setFormData((prev) => ({
                    ...prev,
                    keywords: [...prev.keywords, currentKeyword.trim()]
                }));
                setCurrentKeyword('');
                setError(null);
            } else {
                setError('This keyword already exists');
            }
        }
    }, [currentKeyword, formData.keywords]);

    const handleRemoveKeyword = useCallback((index: number): void => {
        setFormData((prev) => ({
            ...prev,
            keywords: prev.keywords.filter((_, i) => i !== index)
        }));
    }, []);

    const handleKeywordKeyPress = useCallback(
        (e: React.KeyboardEvent<HTMLInputElement>): void => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleAddKeyword();
            }
        },
        [handleAddKeyword]
    );

    const pollForUpdates = useCallback(
        (id: string, count: number): void => {
            pollIntervalRef.current = setInterval(async () => {
                try {
                    const statusResponse = await fetch(`${API_BASE_URL}/api/ranking/tracking-status/${id}`);

                    if (!statusResponse.ok) {
                        throw new Error('Failed to fetch tracking status');
                    }

                    const statusData: TrackingStatus = await statusResponse.json();
                    setTracking(statusData);
                    setPollCount((prev) => prev + 1);

                    if (statusData.status === 'completed' || statusData.status === 'error') {
                        if (pollIntervalRef.current) {
                            clearInterval(pollIntervalRef.current);
                        }

                        try {
                            const resultsResponse = await fetch(
                                `${API_BASE_URL}/api/ranking/tracking-results/${id}`
                            );

                            if (!resultsResponse.ok) {
                                throw new Error('Failed to fetch results');
                            }

                            const resultsData: ResultData = await resultsResponse.json();
                            setResults(resultsData);

                            if (formData.enableNotifications && statusData.status === 'completed') {
                                showNotification(
                                    'Ranking tracking completed!',
                                    `Successfully tracked ${resultsData.summary.found_count} out of ${resultsData.summary.total_keywords} keywords.`
                                );
                            }
                        } catch (resultErr) {
                            const errorMsg =
                                resultErr instanceof Error ? resultErr.message : 'Failed to get results';
                            setError(`Error fetching results: ${errorMsg}`);
                        }

                        setIsLoading(false);
                    }

                    if (count > MAX_POLL_ATTEMPTS) {
                        if (pollIntervalRef.current) {
                            clearInterval(pollIntervalRef.current);
                        }
                        setError('Tracking timeout - please try again');
                        setIsLoading(false);
                    }
                } catch (err) {
                    if (pollIntervalRef.current) {
                        clearInterval(pollIntervalRef.current);
                    }
                    const errorMsg = err instanceof Error ? err.message : 'Unknown polling error';
                    setError(`Polling error: ${errorMsg}`);
                    setIsLoading(false);
                }
            }, POLL_INTERVAL);
        },
        [formData.enableNotifications]
    );

    const handleStartTracking = useCallback(async (): Promise<void> => {
        setError(null);

        if (!formData.businessName.trim()) {
            setError('Business name is required');
            return;
        }

        if (!formData.location.trim()) {
            setError('Location is required');
            return;
        }

        if (formData.keywords.length === 0) {
            setError('Please add at least one keyword');
            return;
        }

        if (formData.useProxy && !formData.proxyIp.trim()) {
            setError('Please enter proxy IP:Port');
            return;
        }

        setIsLoading(true);
        setPollCount(0);

        try {
            const response = await fetch(`${API_BASE_URL}/api/ranking/start-tracking`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
                body: JSON.stringify({
                    business_name: formData.businessName.trim(),
                    location: formData.location.trim(),
                    keywords: formData.keywords,
                    use_proxy: formData.useProxy,
                    proxy_ip: formData.useProxy ? formData.proxyIp.trim() : null,
                    tracking_frequency: formData.trackingFrequency,
                    enable_notifications: formData.enableNotifications
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const errorMsg =
                    (data as ApiError).detail || (data as ApiError).message || 'Failed to start tracking';
                throw new Error(errorMsg);
            }

            const newTrackingId = data.tracking_id;
            setTrackingId(newTrackingId);
            setTracking({
                status: 'started',
                progress: 0,
                total: formData.keywords.length
            });

            pollForUpdates(newTrackingId, 0);
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
            setError(`Error: ${errorMsg}`);
            setIsLoading(false);
        }
    }, [formData, pollForUpdates]);

    const handleLoadPreset = useCallback((): void => {
        setFormData((prev) => ({
            ...prev,
            keywords: [
                'PCOD Treatment',
                'Female Gynaecologist',
                'IVF Treatment',
                'Best Gynaecologist',
                'Infertility Treatment',
                'Gynecology Specialist',
                'Women Health Clinic'
            ]
        }));
        setError(null);
    }, []);

    const handleReset = useCallback((): void => {
        setResults(null);
        setTracking(null);
        setTrackingId(null);
        setPollCount(0);
        setError(null);
        setSortKey('position');
        setSortOrder('asc');
        setFormData({
            businessName: '',
            location: '',
            keywords: [],
            useProxy: false,
            proxyIp: '',
            enableNotifications: true,
            trackingFrequency: 'daily'
        });
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
        }
    }, []);

    const handleExportCSV = useCallback((): void => {
        if (!results) return;

        let csv = 'Keyword,Position,Found,Rank Change,Visibility Score,Timestamp,URL\n';
        results.results.forEach((result) => {
            csv += `"${result.keyword}",${result.position || 'N/A'},${result.found ? 'Yes' : 'No'},${
                result.rank_change || 'N/A'
            },${result.visibility_score || 'N/A'},"${result.timestamp}","${result.url || 'N/A'}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ranking-results-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }, [results]);

    const handleExportJSON = useCallback((): void => {
        if (!results) return;

        const dataStr = JSON.stringify(results, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ranking-results-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }, [results]);

    const showNotification = (title: string, message: string): void => {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    };

    const formatDuration = (seconds: number): string => {
        if (seconds < 60) return `${Math.round(seconds)}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return `${minutes}m ${remainingSeconds}s`;
    };

    const getPositionColor = (position?: number): string => {
        if (!position) return styles.colorGray;
        if (position <= 3) return styles.colorGreen;
        if (position <= 10) return styles.colorBlue;
        if (position <= 50) return styles.colorOrange;
        return styles.colorRed;
    };

    const progressPercentage =
        tracking && tracking.total > 0
            ? (tracking.progress / tracking.total) * 100
            : 0;

    return (
        <div className={styles.wrapper}>
            <div className={styles.container}>
                <div className={styles.header}>
                    <div className={styles.headerContent}>
                        <h1>🎯 Enterprise Ranking Tracker</h1>
                        <p>Advanced real-time SERP monitoring & competitive analysis</p>
                    </div>
                    {results && (
                        <div className={styles.headerStats}>
                            <span className={styles.badge}>
                                <strong>{results.summary.total_keywords}</strong> Keywords
                            </span>
                            <span className={styles.badge}>
                                <strong>{results.summary.found_count}</strong> Ranked
                            </span>
                            <span className={styles.badge}>
                                <strong>{results.summary.success_rate.toFixed(0)}%</strong> Success
                            </span>
                        </div>
                    )}
                </div>

                {error && (
                    <div className={styles.alertError}>
                        <strong>⚠️ Error:</strong> {error}
                    </div>
                )}

                {!results ? (
                    <div className={styles.form}>
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label htmlFor="businessName">Business Name *</label>
                                <input
                                    id="businessName"
                                    type="text"
                                    value={formData.businessName}
                                    onChange={(e) =>
                                        setFormData((prev) => ({
                                            ...prev,
                                            businessName: e.target.value
                                        }))
                                    }
                                    placeholder="e.g., Dr. Prashansa Raut Dalvi"
                                    disabled={isLoading}
                                    aria-label="Business Name"
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label htmlFor="location">Location *</label>
                                <input
                                    id="location"
                                    type="text"
                                    value={formData.location}
                                    onChange={(e) =>
                                        setFormData((prev) => ({
                                            ...prev,
                                            location: e.target.value
                                        }))
                                    }
                                    placeholder="e.g., Malad, Mumbai"
                                    disabled={isLoading}
                                    aria-label="Location"
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label htmlFor="trackingFrequency">Frequency</label>
                                <select
                                    id="trackingFrequency"
                                    value={formData.trackingFrequency}
                                    onChange={(e) =>
                                        setFormData((prev) => ({
                                            ...prev,
                                            trackingFrequency: e.target
                                                .value as 'hourly' | 'daily' | 'weekly'
                                        }))
                                    }
                                    disabled={isLoading}
                                    aria-label="Tracking Frequency"
                                >
                                    <option value="hourly">Hourly</option>
                                    <option value="daily">Daily</option>
                                    <option value="weekly">Weekly</option>
                                </select>
                            </div>
                        </div>

                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label htmlFor="useProxy">
                                    <input
                                        id="useProxy"
                                        type="checkbox"
                                        checked={formData.useProxy}
                                        onChange={(e) =>
                                            setFormData((prev) => ({
                                                ...prev,
                                                useProxy: e.target.checked
                                            }))
                                        }
                                        disabled={isLoading}
                                        aria-label="Use Proxy"
                                    />
                                    Use Mumbai Proxy
                                </label>
                            </div>

                            <div className={styles.formGroup}>
                                <label htmlFor="enableNotifications">
                                    <input
                                        id="enableNotifications"
                                        type="checkbox"
                                        checked={formData.enableNotifications}
                                        onChange={(e) =>
                                            setFormData((prev) => ({
                                                ...prev,
                                                enableNotifications: e.target.checked
                                            }))
                                        }
                                        disabled={isLoading}
                                        aria-label="Enable Notifications"
                                    />
                                    Enable Notifications
                                </label>
                            </div>
                        </div>

                        {formData.useProxy && (
                            <div className={styles.formGroup}>
                                <label htmlFor="proxyIp">Proxy IP:Port *</label>
                                <input
                                    id="proxyIp"
                                    type="text"
                                    value={formData.proxyIp}
                                    onChange={(e) =>
                                        setFormData((prev) => ({
                                            ...prev,
                                            proxyIp: e.target.value
                                        }))
                                    }
                                    placeholder="e.g., 103.28.121.58:8080"
                                    disabled={isLoading}
                                    aria-label="Proxy IP"
                                />
                            </div>
                        )}

                        <div className={styles.formGroup}>
                            <label>Keywords * ({formData.keywords.length} added)</label>
                            <div className={styles.keywordInput}>
                                <input
                                    type="text"
                                    value={currentKeyword}
                                    onChange={(e) => setCurrentKeyword(e.target.value)}
                                    onKeyPress={handleKeywordKeyPress}
                                    placeholder="Enter keyword and press Enter"
                                    disabled={isLoading}
                                    aria-label="Add Keyword"
                                />
                                <button
                                    type="button"
                                    onClick={handleAddKeyword}
                                    disabled={isLoading || !currentKeyword.trim()}
                                    aria-label="Add keyword button"
                                >
                                    Add
                                </button>
                            </div>
                            <div className={styles.keywordsList}>
                                {formData.keywords.map((kw, i) => (
                                    <span
                                        key={`${kw}-${i}`}
                                        className={styles.keywordTag}
                                        role="button"
                                        tabIndex={0}
                                    >
                                        {kw}
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveKeyword(i)}
                                            disabled={isLoading}
                                            aria-label={`Remove keyword ${kw}`}
                                        >
                                            ✕
                                        </button>
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formActions}>
                            <button
                                className={styles.btnPrimary}
                                onClick={handleStartTracking}
                                disabled={isLoading || formData.keywords.length === 0}
                                type="button"
                                aria-label="Start tracking rankings"
                            >
                                {isLoading ? '⏳ Tracking...' : '🚀 Start Tracking'}
                            </button>
                            <button
                                className={styles.btnSecondary}
                                onClick={handleLoadPreset}
                                disabled={isLoading}
                                type="button"
                                aria-label="Load preset keywords"
                            >
                                📋 Load Preset
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className={styles.results}>
                        <div className={styles.resultsHeader}>
                            <h2>📊 Tracking Results</h2>
                            <div className={styles.resultsControls}>
                                <button
                                    className={styles.btnTertiary}
                                    onClick={handleExportCSV}
                                    type="button"
                                    aria-label="Export as CSV"
                                    title="Export as CSV"
                                >
                                    📥 CSV
                                </button>
                                <button
                                    className={styles.btnTertiary}
                                    onClick={handleExportJSON}
                                    type="button"
                                    aria-label="Export as JSON"
                                    title="Export as JSON"
                                >
                                    📤 JSON
                                </button>
                                <button
                                    className={styles.btnTertiary}
                                    onClick={handleReset}
                                    type="button"
                                    aria-label="Start new tracking"
                                    title="New Tracking"
                                >
                                    🔄 New
                                </button>
                            </div>
                        </div>

                        {/* Advanced Statistics */}
                        {stats && (
                            <div className={styles.statsGrid}>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>🥇</div>
                                    <div className={styles.statLabel}>Top 3</div>
                                    <div className={styles.statNumber}>{stats.topThree}</div>
                                </div>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>📄</div>
                                    <div className={styles.statLabel}>Page 1 (1-10)</div>
                                    <div className={styles.statNumber}>{stats.firstPage}</div>
                                </div>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>📊</div>
                                    <div className={styles.statLabel}>Avg Position</div>
                                    <div className={styles.statNumber}>{stats.avgPosition}</div>
                                </div>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>❌</div>
                                    <div className={styles.statLabel}>Not Ranked</div>
                                    <div className={styles.statNumber}>{stats.notRanked}</div>
                                </div>
                            </div>
                        )}

                        {/* Summary Cards */}
                        <div className={styles.summary}>
                            <div className={styles.summaryCard}>
                                <h3>{results.summary.total_keywords}</h3>
                                <p>Total Keywords</p>
                            </div>
                            <div className={styles.summaryCard}>
                                <h3>{results.summary.found_count}</h3>
                                <p>Found Rankings</p>
                            </div>
                            <div className={styles.summaryCard}>
                                <h3>{results.summary.success_rate.toFixed(1)}%</h3>
                                <p>Success Rate</p>
                            </div>
                            {results.summary.execution_time && (
                                <div className={styles.summaryCard}>
                                    <h3>{formatDuration(results.summary.execution_time)}</h3>
                                    <p>Execution Time</p>
                                </div>
                            )}
                        </div>

                        {/* Results Table */}
                        <div className={styles.tableWrapper}>
                            <div className={styles.tableControls}>
                                <label>Sort by:</label>
                                <select
                                    value={sortKey}
                                    onChange={(e) =>
                                        setSortKey(e.target.value as 'position' | 'keyword' | 'timestamp')
                                    }
                                    aria-label="Sort by"
                                >
                                    <option value="position">Position</option>
                                    <option value="keyword">Keyword</option>
                                    <option value="timestamp">Time</option>
                                </select>
                                <button
                                    className={styles.btnSort}
                                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                                    title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
                                >
                                    {sortOrder === 'asc' ? '↑' : '↓'}
                                </button>
                            </div>

                            <div className={styles.resultsTable}>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Keyword</th>
                                            <th>Position</th>
                                            <th>Status</th>
                                            <th>Rank Change</th>
                                            <th>Visibility</th>
                                            <th>Time</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedResults.map((result: RankingResult, i: number) => (
                                            <tr
                                                key={`${result.keyword}-${i}`}
                                                className={`${
                                                    result.found
                                                        ? styles.rowFound
                                                        : styles.rowNotFound
                                                }`}
                                            >
                                                <td>{i + 1}</td>
                                                <td>
                                                    <strong>{result.keyword}</strong>
                                                    {result.url && (
                                                        <small className={styles.urlSmall}>
                                                            {result.url}
                                                        </small>
                                                    )}
                                                </td>
                                                <td>
                                                    {result.found && result.position ? (
                                                        <span
                                                            className={`${styles.positionBadge} ${getPositionColor(
                                                                result.position
                                                            )}`}
                                                        >
                                                            #{result.position}
                                                        </span>
                                                    ) : (
                                                        <span className={styles.positionNone}>—</span>
                                                    )}
                                                </td>
                                                <td>
                                                    <span
                                                        className={`${styles.statusBadge} ${
                                                            result.found
                                                                ? styles.found
                                                                : styles.notFound
                                                        }`}
                                                    >
                                                        {result.found ? '✅ Found' : '❌ Not Found'}
                                                    </span>
                                                </td>
                                                <td>
                                                    {result.rank_change !== undefined && (
                                                        <span
                                                            className={
                                                                result.rank_change > 0
                                                                    ? styles.rankUp
                                                                    : result.rank_change < 0
                                                                      ? styles.rankDown
                                                                      : ''
                                                            }
                                                        >
                                                            {result.rank_change > 0 ? '↑' : '↓'}
                                                            {Math.abs(result.rank_change)}
                                                        </span>
                                                    )}
                                                </td>
                                                <td>
                                                    {result.visibility_score !== undefined && (
                                                        <div className={styles.visibilityBar}>
                                                            <div
                                                                className={styles.visibilityFill}
                                                                style={{
                                                                    width: `${result.visibility_score}%`
                                                                }}
                                                            />
                                                        </div>
                                                    )}
                                                </td>
                                                <td className={styles.timeCell}>
                                                    {new Date(result.timestamp).toLocaleString(
                                                        'en-IN'
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* Progress Tracking */}
                {tracking && !results && (
                    <div className={styles.progress}>
                        <div className={styles.progressContainer}>
                            <div className={styles.progressInfo}>
                                <h3>Tracking Progress</h3>
                                <p>
                                    Status: <strong>{tracking.status.toUpperCase()}</strong>
                                </p>
                                {tracking.current_keyword && (
                                    <p>
                                        Current: <strong>{tracking.current_keyword}</strong>
                                    </p>
                                )}
                                <p>
                                    Progress: <strong>{tracking.progress}</strong> / <strong>{tracking.total}</strong> keywords
                                </p>
                                {tracking.elapsed_time && (
                                    <p>
                                        Elapsed: <strong>{formatDuration(tracking.elapsed_time)}</strong>
                                    </p>
                                )}
                                {tracking.estimated_time_remaining && (
                                    <p>
                                        ETA: <strong>{formatDuration(tracking.estimated_time_remaining)}</strong>
                                    </p>
                                )}
                                <p className={styles.pollInfo}>
                                    Poll #{pollCount} • {new Date().toLocaleTimeString('en-IN')}
                                </p>
                            </div>
                            <div className={styles.progressBarContainer}>
                                <div className={styles.progressBar}>
                                    <div
                                        className={styles.progressFill}
                                        style={{
                                            width: `${Math.min(progressPercentage, 100)}%`,
                                            transition: 'width 0.3s ease'
                                        }}
                                        role="progressbar"
                                        aria-valuenow={Math.round(progressPercentage)}
                                        aria-valuemin={0}
                                        aria-valuemax={100}
                                    />
                                </div>
                                <span className={styles.progressPercent}>
                                    {Math.round(progressPercentage)}%
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

