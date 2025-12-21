/**
 * Performance Monitor Module
 * Tracks and logs performance metrics for the application
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.devMode = this.isDevMode();
        this.timers = new Map();
    }

    /**
     * Check if in development mode
     */
    isDevMode() {
        // Check if running on localhost or with dev parameter
        return window.location.hostname === 'localhost' ||
               window.location.hostname === '127.0.0.1' ||
               window.location.search.includes('dev=true');
    }

    /**
     * Start timing an operation
     */
    startTimer(operationName) {
        const startTime = performance.now();
        this.timers.set(operationName, {
            startTime,
            startMark: `${operationName}-start`
        });

        if (this.supportsPerformanceAPI()) {
            performance.mark(`${operationName}-start`);
        }

        if (this.devMode) {
            console.log(`⏱️ [Performance] Started: ${operationName}`);
        }
    }

    /**
     * End timing an operation
     */
    endTimer(operationName) {
        const endTime = performance.now();
        const timerData = this.timers.get(operationName);

        if (!timerData) {
            console.warn(`No timer found for: ${operationName}`);
            return null;
        }

        const duration = endTime - timerData.startTime;

        if (this.supportsPerformanceAPI()) {
            performance.mark(`${operationName}-end`);
            try {
                performance.measure(
                    operationName,
                    `${operationName}-start`,
                    `${operationName}-end`
                );
            } catch (e) {
                // Ignore measurement errors
            }
        }

        // Store metric
        const metric = {
            name: operationName,
            duration,
            timestamp: new Date().toISOString(),
            memoryUsage: this.getMemoryUsage()
        };

        this.metrics.set(operationName, metric);

        if (this.devMode) {
            console.log(`✅ [Performance] Completed: ${operationName} - ${duration.toFixed(2)}ms`);
            this.logMetric(metric);
        }

        // Clean up
        this.timers.delete(operationName);

        return metric;
    }

    /**
     * Record a custom metric
     */
    recordMetric(name, value, unit = 'ms') {
        const metric = {
            name,
            value,
            unit,
            timestamp: new Date().toISOString(),
            memoryUsage: this.getMemoryUsage()
        };

        this.metrics.set(name, metric);

        if (this.devMode) {
            console.log(`📊 [Performance] Metric: ${name} = ${value}${unit}`);
        }

        return metric;
    }

    /**
     * Track upload performance
     */
    trackUpload(fileSize, duration) {
        const uploadSpeed = fileSize / (duration / 1000); // bytes per second
        const uploadSpeedMBps = (uploadSpeed / (1024 * 1024)).toFixed(2);

        this.recordMetric('upload-size', fileSize, 'bytes');
        this.recordMetric('upload-duration', duration, 'ms');
        this.recordMetric('upload-speed', uploadSpeedMBps, 'MB/s');

        if (this.devMode) {
            console.group('📤 Upload Performance');
            console.log(`File Size: ${(fileSize / (1024 * 1024)).toFixed(2)} MB`);
            console.log(`Duration: ${(duration / 1000).toFixed(2)} seconds`);
            console.log(`Speed: ${uploadSpeedMBps} MB/s`);
            console.groupEnd();
        }
    }

    /**
     * Track processing performance
     */
    trackProcessing(audioDuration, processingTime, stages = {}) {
        const rtf = processingTime / audioDuration; // Real-time factor

        this.recordMetric('audio-duration', audioDuration, 's');
        this.recordMetric('processing-time', processingTime, 's');
        this.recordMetric('rtf', rtf.toFixed(2), 'x');

        Object.entries(stages).forEach(([stage, duration]) => {
            this.recordMetric(`stage-${stage}`, duration, 's');
        });

        if (this.devMode) {
            console.group('⚙️ Processing Performance');
            console.log(`Audio Duration: ${audioDuration.toFixed(2)}s`);
            console.log(`Processing Time: ${processingTime.toFixed(2)}s`);
            console.log(`Real-time Factor: ${rtf.toFixed(2)}x`);
            console.log('Stages:', stages);
            console.groupEnd();
        }
    }

    /**
     * Track API response time
     */
    trackAPICall(endpoint, duration, success = true) {
        const metricName = `api-${endpoint}`;

        this.recordMetric(`${metricName}-duration`, duration, 'ms');
        this.recordMetric(`${metricName}-success`, success ? 1 : 0, 'bool');

        if (this.devMode) {
            const icon = success ? '✅' : '❌';
            console.log(`${icon} [API] ${endpoint} - ${duration.toFixed(2)}ms`);
        }
    }

    /**
     * Track UI render time
     */
    trackUIRender(componentName, duration) {
        this.recordMetric(`ui-${componentName}`, duration, 'ms');

        if (this.devMode) {
            console.log(`🎨 [UI] ${componentName} rendered in ${duration.toFixed(2)}ms`);
        }
    }

    /**
     * Get memory usage (if available)
     */
    getMemoryUsage() {
        if (performance.memory) {
            return {
                usedJSHeapSize: performance.memory.usedJSHeapSize,
                totalJSHeapSize: performance.memory.totalJSHeapSize,
                jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
            };
        }
        return null;
    }

    /**
     * Get all metrics
     */
    getMetrics() {
        return Array.from(this.metrics.values());
    }

    /**
     * Get specific metric
     */
    getMetric(name) {
        return this.metrics.get(name);
    }

    /**
     * Generate performance report
     */
    generateReport() {
        const metrics = this.getMetrics();

        if (metrics.length === 0) {
            return 'No performance metrics recorded yet.';
        }

        const report = {
            timestamp: new Date().toISOString(),
            totalMetrics: metrics.length,
            metrics: metrics,
            summary: this.generateSummary(metrics),
            memory: this.getMemoryUsage()
        };

        if (this.devMode) {
            console.group('📈 Performance Report');
            console.table(metrics.map(m => ({
                Name: m.name,
                Value: m.value !== undefined ? `${m.value}${m.unit}` : `${m.duration.toFixed(2)}ms`,
                Timestamp: m.timestamp
            })));
            console.log('Summary:', report.summary);
            console.log('Memory:', report.memory);
            console.groupEnd();
        }

        return report;
    }

    /**
     * Generate summary statistics
     */
    generateSummary(metrics) {
        const summary = {};

        // Group by category
        const categories = {
            upload: metrics.filter(m => m.name.startsWith('upload-')),
            processing: metrics.filter(m => m.name.startsWith('stage-') || m.name === 'processing-time'),
            api: metrics.filter(m => m.name.startsWith('api-')),
            ui: metrics.filter(m => m.name.startsWith('ui-'))
        };

        Object.entries(categories).forEach(([category, items]) => {
            if (items.length > 0) {
                const durations = items
                    .filter(m => m.duration !== undefined)
                    .map(m => m.duration);

                if (durations.length > 0) {
                    summary[category] = {
                        count: items.length,
                        totalDuration: durations.reduce((a, b) => a + b, 0),
                        avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
                        minDuration: Math.min(...durations),
                        maxDuration: Math.max(...durations)
                    };
                }
            }
        });

        return summary;
    }

    /**
     * Display performance metrics in UI
     */
    displayMetrics(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const report = this.generateReport();
        if (typeof report === 'string') {
            container.innerHTML = `<p>${report}</p>`;
            return;
        }

        const metricsHTML = `
            <div class="performance-metrics">
                <h4>Performance Metrics</h4>
                <div class="metrics-grid">
                    ${report.metrics.map(m => `
                        <div class="metric-card">
                            <div class="metric-name">${this.formatMetricName(m.name)}</div>
                            <div class="metric-value">
                                ${m.value !== undefined ? `${m.value}${m.unit}` : `${m.duration.toFixed(2)}ms`}
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${report.memory ? `
                    <div class="memory-usage">
                        <h5>Memory Usage</h5>
                        <p>Used: ${(report.memory.usedJSHeapSize / (1024 * 1024)).toFixed(2)} MB</p>
                        <p>Total: ${(report.memory.totalJSHeapSize / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                ` : ''}
            </div>
        `;

        container.innerHTML = metricsHTML;
    }

    /**
     * Format metric name for display
     */
    formatMetricName(name) {
        return name
            .replace(/-/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Log metric to console (dev mode)
     */
    logMetric(metric) {
        if (!this.devMode) return;

        const value = metric.value !== undefined
            ? `${metric.value}${metric.unit}`
            : `${metric.duration.toFixed(2)}ms`;

        console.log(`📊 ${metric.name}: ${value}`);

        if (metric.memoryUsage) {
            const usedMB = (metric.memoryUsage.usedJSHeapSize / (1024 * 1024)).toFixed(2);
            console.log(`   Memory: ${usedMB} MB`);
        }
    }

    /**
     * Check if Performance API is supported
     */
    supportsPerformanceAPI() {
        return typeof performance !== 'undefined' &&
               typeof performance.mark === 'function' &&
               typeof performance.measure === 'function';
    }

    /**
     * Clear all metrics
     */
    clearMetrics() {
        this.metrics.clear();
        this.timers.clear();

        if (this.supportsPerformanceAPI()) {
            performance.clearMarks();
            performance.clearMeasures();
        }

        if (this.devMode) {
            console.log('🗑️ [Performance] Metrics cleared');
        }
    }

    /**
     * Export metrics as JSON
     */
    exportMetrics() {
        const report = this.generateReport();
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance-metrics-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Export for global access
window.PerformanceMonitor = PerformanceMonitor;
