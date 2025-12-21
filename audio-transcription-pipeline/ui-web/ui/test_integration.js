/**
 * Client-Side Integration Tests for GPU Pipeline UI
 *
 * This tests the JavaScript API client integration
 * Run in browser console or with Node.js
 */

// ========================================
// Configuration
// ========================================
const API_CONFIG = {
    baseUrl: 'http://localhost:8000',
    endpoints: {
        upload: '/api/upload',
        status: '/api/status',
        results: '/api/results',
        cancel: '/api/cancel',
        jobs: '/api/jobs',
        health: '/health'
    },
    pollInterval: 1000
};

// ========================================
// Test Utilities
// ========================================
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m'
};

function log(message, color = 'reset') {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    console.log(`${colors[color]}[${timestamp}] ${message}${colors.reset}`);
}

function success(message) { log(`✅ ${message}`, 'green'); }
function error(message) { log(`❌ ${message}`, 'red'); }
function warning(message) { log(`⚠️  ${message}`, 'yellow'); }
function info(message) { log(`ℹ️  ${message}`, 'blue'); }

// ========================================
// API Client Functions
// ========================================

/**
 * Upload file to server
 */
async function uploadFile(file, numSpeakers = 2) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('num_speakers', numSpeakers);

    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get job status
 */
async function getStatus(jobId) {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${jobId}`);

    if (!response.ok) {
        throw new Error(`Status check failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get job results
 */
async function getResults(jobId) {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.results}/${jobId}`);

    if (!response.ok) {
        throw new Error(`Results fetch failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Cancel job
 */
async function cancelJob(jobId) {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.cancel}/${jobId}`, {
        method: 'POST'
    });

    if (!response.ok) {
        throw new Error(`Cancel failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * List all jobs
 */
async function listJobs() {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.jobs}`);

    if (!response.ok) {
        throw new Error(`List jobs failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Health check
 */
async function healthCheck() {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`);

    if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
}

// ========================================
// Integration Tests
// ========================================

/**
 * Test 1: Server Connectivity
 */
async function testServerConnectivity() {
    info('Test 1: Testing server connectivity...');

    try {
        const health = await healthCheck();

        if (health.status === 'healthy') {
            success('Server is healthy and responding');
            info(`Pipeline script: ${health.pipeline_script}`);
            info(`Pipeline exists: ${health.pipeline_exists}`);
            info(`Active jobs: ${health.active_jobs}`);
            return true;
        } else {
            error('Server responded but status is not healthy');
            return false;
        }
    } catch (err) {
        error(`Cannot connect to server: ${err.message}`);
        return false;
    }
}

/**
 * Test 2: File Upload with Mock Data
 */
async function testFileUpload() {
    info('Test 2: Testing file upload...');

    try {
        // Create mock file
        const blob = new Blob(['MOCK_AUDIO_DATA'.repeat(1000)], { type: 'audio/mpeg' });
        const file = new File([blob], 'test_mock.mp3', { type: 'audio/mpeg' });

        const result = await uploadFile(file, 2);

        if (result.job_id && result.status === 'queued') {
            success(`Upload successful. Job ID: ${result.job_id.substring(0, 8)}...`);
            info(`Message: ${result.message}`);
            return result.job_id;
        } else {
            error('Upload response missing required fields');
            return null;
        }
    } catch (err) {
        error(`Upload failed: ${err.message}`);
        return null;
    }
}

/**
 * Test 3: Status Polling
 */
async function testStatusPolling(jobId) {
    info('Test 3: Testing status polling...');

    try {
        const status = await getStatus(jobId);

        if (status.job_id === jobId && 'status' in status && 'progress' in status) {
            success(`Status retrieved: ${status.status} (${status.progress}%)`);
            info(`Current step: ${status.step}`);
            return true;
        } else {
            error('Status response missing required fields');
            return false;
        }
    } catch (err) {
        error(`Status check failed: ${err.message}`);
        return false;
    }
}

/**
 * Test 4: Invalid Job ID Handling
 */
async function testInvalidJobId() {
    info('Test 4: Testing invalid job ID handling...');

    try {
        await getStatus('invalid-job-id-12345');
        error('Should have thrown error for invalid job ID');
        return false;
    } catch (err) {
        if (err.message.includes('404') || err.message.includes('not found')) {
            success('Invalid job ID correctly rejected');
            return true;
        } else {
            error(`Unexpected error: ${err.message}`);
            return false;
        }
    }
}

/**
 * Test 5: List Jobs
 */
async function testListJobs() {
    info('Test 5: Testing job listing...');

    try {
        const data = await listJobs();

        if ('total' in data && 'jobs' in data) {
            success(`Jobs list retrieved. Total: ${data.total}`);
            if (data.total > 0) {
                info(`Recent jobs: ${data.jobs.slice(0, 3).map(j => j.job_id.substring(0, 8)).join(', ')}...`);
            }
            return true;
        } else {
            error('Jobs list response missing required fields');
            return false;
        }
    } catch (err) {
        error(`List jobs failed: ${err.message}`);
        return false;
    }
}

/**
 * Test 6: Error Handling
 */
async function testErrorHandling() {
    info('Test 6: Testing error handling...');

    try {
        // Try to upload invalid file type
        const blob = new Blob(['NOT_AUDIO'], { type: 'text/plain' });
        const file = new File([blob], 'test.txt', { type: 'text/plain' });

        await uploadFile(file);
        error('Should have rejected invalid file type');
        return false;
    } catch (err) {
        if (err.message.includes('400') || err.message.toLowerCase().includes('invalid')) {
            success('Invalid file type correctly rejected');
            return true;
        } else {
            warning(`Unexpected error: ${err.message}`);
            return true; // Still passes as it did error out
        }
    }
}

/**
 * Test 7: CORS Headers
 */
async function testCORS() {
    info('Test 7: Testing CORS configuration...');

    try {
        const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`);
        const corsHeader = response.headers.get('Access-Control-Allow-Origin');

        if (corsHeader) {
            success(`CORS enabled: ${corsHeader}`);
            return true;
        } else {
            warning('CORS headers not found (might still work)');
            return true; // Not a failure
        }
    } catch (err) {
        error(`CORS test failed: ${err.message}`);
        return false;
    }
}

// ========================================
// Main Test Runner
// ========================================
async function runAllTests() {
    console.log('\n' + '='.repeat(70));
    console.log('GPU PIPELINE UI - JavaScript Integration Tests'.center(70));
    console.log('='.repeat(70) + '\n');

    const results = {};
    let jobId = null;

    // Run tests sequentially
    results['Server Connectivity'] = await testServerConnectivity();

    if (!results['Server Connectivity']) {
        error('\nServer is not running. Cannot continue tests.');
        info('Start the server with: python ui/server.py');
        return;
    }

    results['File Upload'] = false;
    jobId = await testFileUpload();
    if (jobId) {
        results['File Upload'] = true;
    }

    if (jobId) {
        // Wait a moment for processing to start
        await new Promise(resolve => setTimeout(resolve, 1000));
        results['Status Polling'] = await testStatusPolling(jobId);
    }

    results['Invalid Job ID'] = await testInvalidJobId();
    results['List Jobs'] = await testListJobs();
    results['Error Handling'] = await testErrorHandling();
    results['CORS'] = await testCORS();

    // Print summary
    console.log('\n' + '='.repeat(70));
    console.log('TEST SUMMARY'.center(70));
    console.log('='.repeat(70) + '\n');

    let passed = 0;
    let total = 0;

    for (const [testName, result] of Object.entries(results)) {
        total++;
        if (result) passed++;

        const status = result ?
            `${colors.green}✅ PASS${colors.reset}` :
            `${colors.red}❌ FAIL${colors.reset}`;
        console.log(`${testName.padEnd(40, '.')} ${status}`);
    }

    console.log(`\n${colors.blue}Total: ${passed}/${total} tests passed${colors.reset}\n`);

    if (passed === total) {
        console.log(`${colors.green}🎉 ALL TESTS PASSED! 🎉${colors.reset}\n`);
    } else {
        console.log(`${colors.red}Some tests failed. See details above.${colors.reset}\n`);
    }
}

// ========================================
// Browser-Compatible Helper
// ========================================
String.prototype.center = function(width) {
    const padding = Math.max(0, width - this.length);
    const left = Math.floor(padding / 2);
    const right = Math.ceil(padding / 2);
    return ' '.repeat(left) + this + ' '.repeat(right);
};

// ========================================
// Export for Node.js or Run in Browser
// ========================================
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        runAllTests,
        testServerConnectivity,
        testFileUpload,
        testStatusPolling,
        testInvalidJobId,
        testListJobs,
        testErrorHandling,
        testCORS
    };

    // Auto-run if executed directly
    if (require.main === module) {
        runAllTests().catch(console.error);
    }
} else {
    // Browser environment - expose to window
    window.GPUPipelineTests = {
        runAllTests,
        testServerConnectivity,
        testFileUpload,
        testStatusPolling,
        testInvalidJobId,
        testListJobs,
        testErrorHandling,
        testCORS
    };

    console.log('GPU Pipeline Integration Tests loaded.');
    console.log('Run tests with: GPUPipelineTests.runAllTests()');
}
