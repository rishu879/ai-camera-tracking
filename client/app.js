/**
 * ISRO FSOC Mission Control Console Frontend Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let isTrackingEnabled = true;
    let isOccluded = false;
    let pollInterval = null;

    // --- DOM Elements ---
    const streamImg = document.getElementById('live-stream');
    const systemStatusText = document.getElementById('system-status-text');
    const isroComplianceBadge = document.getElementById('isro-compliance-badge');
    const telError = document.getElementById('tel-error');
    const telFps = document.getElementById('tel-fps');
    const telLock = document.getElementById('tel-lock');
    const telPtz = document.getElementById('tel-ptz');
    const telLatency = document.getElementById('tel-latency');
    const telCpu = document.getElementById('tel-cpu');

    // Controls
    const btnToggleTracking = document.getElementById('btn-toggle-tracking');
    const btnInjectOcclusion = document.getElementById('btn-inject-occlusion');
    const btnReset = document.getElementById('btn-reset');

    // Sliders & Value Displays
    const sliders = [
        { id: 'slider-fog', valId: 'val-fog', key: 'fog_density', unit: '', multiplier: 1 },
        { id: 'slider-rain', valId: 'val-rain', key: 'rain_intensity', unit: '', multiplier: 1 },
        { id: 'slider-snow', valId: 'val-snow', key: 'snow_intensity', unit: '', multiplier: 1 },
        { id: 'slider-haze', valId: 'val-haze', key: 'haze_density', unit: '', multiplier: 1 },
        { id: 'slider-gaussian', valId: 'val-gaussian', key: 'gaussian_std', unit: ' px', multiplier: 1 },
        { id: 'slider-saltpepper', valId: 'val-saltpepper', key: 'salt_pepper_ratio', unit: '%', multiplier: 100 },
        { id: 'slider-motionblur', valId: 'val-motionblur', key: 'motion_blur_kernel', unit: ' px', multiplier: 1, isInt: true },
        { id: 'slider-camerablur', valId: 'val-camerablur', key: 'camera_blur_sigma', unit: ' px', multiplier: 1 },
        { id: 'slider-speed', valId: 'val-speed', key: 'target_speed', unit: ' px/s', multiplier: 1 },
        { id: 'slider-panspeed', valId: 'val-panspeed', key: 'max_pan_speed', unit: '°/s', multiplier: 1 },
        { id: 'slider-tiltspeed', valId: 'val-tiltspeed', key: 'max_tilt_speed', unit: '°/s', multiplier: 1 }
    ];

    const chkLowlight = document.getElementById('chk-lowlight');
    const selectMotion = document.getElementById('select-motion');

    // Benchmarks
    const btnRunBenchmark1 = document.getElementById('btn-run-benchmark1');
    const bench1Status = document.getElementById('benchmark1-status');
    const bench2File = document.getElementById('bench2-file');
    const btnRunBenchmark2 = document.getElementById('btn-run-benchmark2');
    const bench2Status = document.getElementById('benchmark2-status');

    // Reports
    const btnRefreshReports = document.getElementById('btn-refresh-reports');
    const reportsList = document.getElementById('reports-list');

    // --- Tab Switching ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');
            tabButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');

            if (targetId === 'tab-reports') {
                loadReports();
            }
        });
    });

    // --- Config Update Helper ---
    async function updateConfig(payload) {
        try {
            await fetch('/api/config/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (err) {
            console.error('Failed to update config:', err);
        }
    }

    // --- Stream Auto-Reconnect & Resilience ---
    if (streamImg) {
        streamImg.onerror = () => {
            console.warn('Stream interrupted, attempting reconnection in 1s...');
            setTimeout(() => {
                streamImg.src = '/api/stream?t=' + Date.now();
            }, 1000);
        };
    }

    // --- Wire Sliders with Debounced Realtime Updates ---
    sliders.forEach(item => {
        const sliderEl = document.getElementById(item.id);
        const valEl = document.getElementById(item.valId);
        if (!sliderEl || !valEl) return;

        let debounceTimer = null;

        sliderEl.addEventListener('input', () => {
            const rawVal = item.isInt 
                ? parseInt(sliderEl.value, 10) 
                : parseFloat(sliderEl.value);
            const displayVal = item.multiplier === 100 
                ? (rawVal * 100).toFixed(0) 
                : rawVal;
            valEl.textContent = `${displayVal}${item.unit}`;

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                updateConfig({ [item.key]: rawVal });
            }, 80);
        });

        sliderEl.addEventListener('change', () => {
            const rawVal = item.isInt 
                ? parseInt(sliderEl.value, 10) 
                : parseFloat(sliderEl.value);
            clearTimeout(debounceTimer);
            updateConfig({ [item.key]: rawVal });
        });
    });

    if (chkLowlight) {
        chkLowlight.addEventListener('change', () => {
            updateConfig({ low_light: chkLowlight.checked });
        });
    }

    if (selectMotion) {
        selectMotion.addEventListener('change', () => {
            updateConfig({ motion_type: selectMotion.value });
        });
    }

    // --- Viewport Actions ---
    btnToggleTracking.addEventListener('click', async () => {
        isTrackingEnabled = !isTrackingEnabled;
        btnToggleTracking.textContent = isTrackingEnabled ? 'Pause Servo' : 'Resume Servo';
        await updateConfig({ tracking_enabled: isTrackingEnabled });
    });

    btnInjectOcclusion.addEventListener('click', async () => {
        isOccluded = !isOccluded;
        btnInjectOcclusion.textContent = isOccluded ? 'Clear Occlusion' : 'Inject Cloud Occlusion';
        if (isOccluded) {
            btnInjectOcclusion.classList.add('btn-danger');
        } else {
            btnInjectOcclusion.classList.remove('btn-danger');
        }
        await updateConfig({ is_occluded: isOccluded });
    });

    btnReset.addEventListener('click', async () => {
        try {
            await fetch('/api/system/reset', { method: 'POST' });
            isOccluded = false;
            btnInjectOcclusion.textContent = 'Inject Cloud Occlusion';
            btnInjectOcclusion.classList.remove('btn-danger');
            if (streamImg) {
                streamImg.src = '/api/stream?t=' + Date.now();
            }
        } catch (err) {
            console.error('Reset failed:', err);
        }
    });

    // --- Telemetry Poller ---
    async function pollTelemetry() {
        try {
            const res = await fetch('/api/state');
            if (!res.ok) return;
            const data = await res.json();

            // Update Metrics
            if (data.tracking_error_px !== undefined) {
                telError.textContent = `${data.tracking_error_px} px`;
                const errCard = telError.parentElement;
                errCard.classList.remove('compliant', 'warning', 'alert');
                if (data.tracking_error_px <= 10.0) {
                    errCard.classList.add('compliant');
                } else if (data.tracking_error_px <= 20.0) {
                    errCard.classList.add('warning');
                } else {
                    errCard.classList.add('alert');
                }
            }

            if (data.fps !== undefined) {
                telFps.textContent = `${data.fps} FPS`;
                const fpsCard = telFps.parentElement;
                fpsCard.classList.remove('compliant', 'warning', 'alert');
                if (data.fps >= 25.0) {
                    fpsCard.classList.add('compliant');
                } else if (data.fps >= 20.0) {
                    fpsCard.classList.add('warning');
                } else {
                    fpsCard.classList.add('alert');
                }
            }

            if (data.summary && data.summary.lock_retention_rate !== undefined) {
                const lockPct = (data.summary.lock_retention_rate * 100).toFixed(1);
                telLock.textContent = `${lockPct}%`;
                const lockCard = telLock.parentElement;
                lockCard.classList.remove('compliant', 'alert');
                if (data.summary.lock_retention_rate >= 0.95) {
                    lockCard.classList.add('compliant');
                } else {
                    lockCard.classList.add('alert');
                }
            }

            if (data.pan_deg !== undefined && data.tilt_deg !== undefined) {
                telPtz.textContent = `${data.pan_deg > 0 ? '+' : ''}${data.pan_deg.toFixed(2)}° / ${data.tilt_deg > 0 ? '+' : ''}${data.tilt_deg.toFixed(2)}°`;
            }

            if (data.latency_ms !== undefined) {
                telLatency.textContent = `${data.latency_ms} ms`;
            }

            if (data.frame_idx !== undefined) {
                telCpu.textContent = `Frame: #${data.frame_idx}`;
            }

            // Update System Status Text
            if (data.is_occluded) {
                systemStatusText.textContent = 'OCCLUSION DETECTED: COASTING';
                systemStatusText.style.color = '#ffaa00';
            } else if (!data.tracking_enabled) {
                systemStatusText.textContent = 'SERVO CONTROL: PAUSED';
                systemStatusText.style.color = '#ff3d71';
            } else if (data.is_locked) {
                systemStatusText.textContent = 'CLOSED-LOOP SERVO: LOCKED';
                systemStatusText.style.color = '#00e676';
            } else {
                systemStatusText.textContent = 'COARSE ACQUISITION: SEARCHING';
                systemStatusText.style.color = '#00e5ff';
            }

            // Compliance Badge
            const isCompliant = (data.tracking_error_px <= 10.0) && (data.fps >= 20.0);
            if (isCompliant) {
                isroComplianceBadge.textContent = 'ISRO SPEC: COMPLIANT';
                isroComplianceBadge.classList.remove('non-compliant');
            } else {
                isroComplianceBadge.textContent = 'ISRO SPEC: CONVERGING';
                isroComplianceBadge.classList.add('non-compliant');
            }

        } catch (err) {
            // Server might be reloading
        }
    }

    // Start Polling every 200ms
    pollInterval = setInterval(pollTelemetry, 200);

    // --- Benchmark 1 ---
    btnRunBenchmark1.addEventListener('click', async () => {
        bench1Status.className = 'status-msg info';
        bench1Status.textContent = 'Executing ISRO Benchmark-1 (180 frames under figure-8 kinematics, fog & jitter)...';
        btnRunBenchmark1.disabled = true;

        try {
            const res = await fetch('/api/benchmark1/run?frames=180', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                const s = data.results.benchmark_summary;
                bench1Status.className = 'status-msg success';
                bench1Status.innerHTML = `
                    <strong>✓ Benchmark-1 Completed!</strong><br>
                    • Mean Tracking Error: ${s.mean_tracking_error_px} px (Target &le; 10 px)<br>
                    • Mean Throughput: ${s.mean_fps} FPS (Target &ge; 20 FPS)<br>
                    • Lock Retention Rate: ${(s.lock_retention_rate * 100).toFixed(1)}% (Target &gt; 95%)<br>
                    • Overall Compliance: <strong>${s.overall_compliant ? 'PASSED (ISRO COMPLIANT)' : 'NEEDS TUNING'}</strong><br>
                    <em>Report compiled in Reports tab.</em>
                `;
                loadReports();
            } else {
                bench1Status.className = 'status-msg error';
                bench1Status.textContent = 'Benchmark execution failed: ' + (data.message || 'Unknown error');
            }
        } catch (err) {
            bench1Status.className = 'status-msg error';
            bench1Status.textContent = 'Failed to execute Benchmark-1: ' + err.message;
        } finally {
            btnRunBenchmark1.disabled = false;
        }
    });

    // --- Benchmark 2 ---
    btnRunBenchmark2.addEventListener('click', async () => {
        const file = bench2File.files[0];
        if (!file) {
            bench2Status.className = 'status-msg error';
            bench2Status.textContent = 'Please select an .mp4 video file first.';
            return;
        }

        bench2Status.className = 'status-msg info';
        bench2Status.textContent = `Uploading "${file.name}" & executing Benchmark-2 Coarse Pointing evaluation...`;
        btnRunBenchmark2.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/benchmark2/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.status === 'success') {
                const s = data.results.benchmark_summary;
                bench2Status.className = 'status-msg success';
                bench2Status.innerHTML = `
                    <strong>✓ Benchmark-2 Evaluated!</strong><br>
                    • Total Frames Processed: ${s.total_frames}<br>
                    • Mean Centroid Error: ${s.mean_tracking_error_px} px<br>
                    • Processing Throughput: ${s.mean_fps} FPS<br>
                    • Detection Success: ${(s.lock_retention_rate * 100).toFixed(1)}%<br>
                    <em>Annotated video and metrics generated.</em>
                `;
                loadReports();
            } else {
                bench2Status.className = 'status-msg error';
                bench2Status.textContent = 'Benchmark-2 failed: ' + (data.message || 'Unknown error');
            }
        } catch (err) {
            bench2Status.className = 'status-msg error';
            bench2Status.textContent = 'Failed to run Benchmark-2: ' + err.message;
        } finally {
            btnRunBenchmark2.disabled = false;
        }
    });

    // --- Reports Loader ---
    async function loadReports() {
        if (!reportsList) return;
        reportsList.innerHTML = '<div class="loading-text">Loading report archive...</div>';

        try {
            const res = await fetch('/api/reports/list');
            if (!res.ok) throw new Error('Failed to fetch reports');
            const items = await res.json();

            if (items.length === 0) {
                reportsList.innerHTML = '<div class="loading-text">No evaluation reports generated yet. Run Benchmark-1 to generate one!</div>';
                return;
            }

            reportsList.innerHTML = '';
            items.forEach(item => {
                const row = document.createElement('div');
                row.className = 'report-item';
                
                let actionsHtml = '';
                if (item.has_pdf) {
                    actionsHtml += `<a href="${item.pdf_url}" target="_blank" class="btn btn-outline btn-sm">PDF Report</a>`;
                }
                if (item.has_html) {
                    actionsHtml += `<a href="${item.html_url}" target="_blank" class="btn btn-primary btn-sm">Interactive Dashboard</a>`;
                }

                row.innerHTML = `
                    <div class="name">📄 ${item.session_name}</div>
                    <div class="report-actions">${actionsHtml}</div>
                `;
                reportsList.appendChild(row);
            });
        } catch (err) {
            reportsList.innerHTML = `<div class="status-msg error">Failed to load reports: ${err.message}</div>`;
        }
    }

    if (btnRefreshReports) {
        btnRefreshReports.addEventListener('click', loadReports);
    }
});
