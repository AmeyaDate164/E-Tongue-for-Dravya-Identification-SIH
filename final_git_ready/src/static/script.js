```javascript
let myRadarChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Config
    try {
        const resp = await fetch('/get_config');
        const config = await resp.json();
        
        if(config.camera_url) {
            const el = document.getElementById('cameraUrl');
            if(el) el.value = config.camera_url;
        }
        
        if(config.blank_rgb) {
            const [r, g, b] = config.blank_rgb;
            document.getElementById('blankR').value = r;
            document.getElementById('blankG').value = g;
            document.getElementById('blankB').value = b;
        }
        
        if(config.coordinates) {
            for(const [r, coords] of Object.entries(config.coordinates)) {
                // Selector: data-r="1"
                const inpX = document.querySelector(`.coord - input[data - r="${r}"][data - axis="x"]`);
                const inpY = document.querySelector(`.coord - input[data - r="${r}"][data - axis="y"]`);
                if(inpX) inpX.value = coords.x;
                if(inpY) inpY.value = coords.y;
            }
        }
    } catch(err) {
        console.log("No config loaded", err);
    }

    // Manual Form
    const manualForm = document.getElementById('predictionForm');
    if (manualForm) {
        manualForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(manualForm);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value || 0;
            });

            await handlePrediction('/predict', data);
        });
    }

    // Auto Form
    const autoForm = document.getElementById('autoForm');
    if(autoForm) {
        autoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Gather Config
            const cameraUrl = document.getElementById('cameraUrl').value;
            const blankR = parseFloat(document.getElementById('blankR').value) || 255;
            const blankG = parseFloat(document.getElementById('blankG').value) || 255;
            const blankB = parseFloat(document.getElementById('blankB').value) || 255;
            const continuous = document.getElementById('continuousMode').checked;
            const interval = parseFloat(document.getElementById('refreshInterval').value) || 5;

            // Gather Coordinates
            const coords = {};
            const coordInputs = document.querySelectorAll('.coord-input');
            coordInputs.forEach(inp => {
                const r = inp.dataset.r;
                const axis = inp.dataset.axis;
                if(!coords[r]) coords[r] = {};
                coords[r][axis] = parseFloat(inp.value) || 0;
            });
            
            const payload = {
                camera_url: cameraUrl,
                blank_rgb: [blankR, blankG, blankB],
                coordinates: coords
            };
            
            if(continuous) {
                startContinuous(payload, interval);
            } else {
                await handlePrediction('/analyze_image', payload);
            }
        });
    }

    // Init Chart
    const ctx = document.getElementById('radarChart').getContext('2d');
    initChart(ctx);
});

let autoTimer = null;
let isRunning = false;

async function startContinuous(payload, intervalSec) {
    if(isRunning) return;
    isRunning = true;
    
    document.getElementById('btnStartAuto').style.display = 'none';
    document.getElementById('btnStopAuto').style.display = 'block';
    
    const runLoop = async () => {
        if(!isRunning) return;
        
        try {
            await handlePrediction('/analyze_image', payload, true);
        } catch(e) {
            console.error("Auto loop error", e);
        }
        
        if(isRunning) {
            // Visualize countdown or just wait
            const btn = document.getElementById('btnStopAuto');
            btn.textContent = `Running... (Next in ${ intervalSec }s)`;
            autoTimer = setTimeout(runLoop, intervalSec * 1000);
        }
    };
    
    runLoop();
}

function stopContinuous() {
    isRunning = false;
    clearTimeout(autoTimer);
    document.getElementById('btnStartAuto').style.display = 'block';
    document.getElementById('btnStopAuto').style.display = 'none';
    document.getElementById('btnStopAuto').textContent = "Stop";
}


async function handlePrediction(endpoint, data, isAuto = false) {
    const btn = document.querySelector('.tab-content.active .btn-predict');
    // If auto, we might use a different button or no UI block
    let originalText = "Start Auto Analysis";
    
    if(!isAuto && btn) {
        originalText = btn.textContent;
        btn.textContent = "Analyzing...";
        btn.disabled = true;
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.status === 'success') {
            updateUI(result.result);
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during analysis.');
    } finally {
        if(!isAuto && btn) {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }
}

function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(tab + '-tab').classList.add('active');

    // Toggle Button Active State
    const buttons = document.querySelectorAll('.tab-btn');
    if (tab === 'manual') {
        buttons[0].classList.add('active');
    } else {
        buttons[1].classList.add('active');
    }
}

function initChart(ctx) {
    myRadarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Sour', 'Sweet', 'Bitter', 'Salty', 'Pungent', 'Astringent'],
            datasets: [{
                label: 'Taste Profile',
                data: [0, 0, 0, 0, 0, 0],
                fill: true,
                backgroundColor: 'rgba(30, 136, 229, 0.2)',
                borderColor: '#1E88E5',
                pointBackgroundColor: '#1E88E5',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#1E88E5'
            }]
        },
        options: {
            elements: {
                line: { borderWidth: 3 }
            },
            scales: {
                r: {
                    angleLines: { color: '#EEEEEE' },
                    grid: { color: '#EEEEEE' },
                    pointLabels: {
                        font: { size: 12, family: "'Inter', sans-serif", weight: '600' },
                        color: '#333'
                    },
                    suggestedMin: 0,
                    suggestedMax: 1
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function updateUI(data) {
    // Update Text
    const taste = data.predicted_taste;
    const confidence = (data.confidence * 100).toFixed(1);

    const predTaste = document.getElementById('predTaste');
    const predConf = document.getElementById('predConf');
    const confBar = document.getElementById('confBar');

    predTaste.textContent = taste;
    predConf.textContent = `${ confidence }% Confidence`;
    confBar.style.width = `${ confidence }% `;

    // Fill Manual Form with Extracted Data (if available) for verification
    if (data.extraction_details) {
        for (const [key, info] of Object.entries(data.extraction_details)) {
            const input = document.querySelector(`input[name = "${key}"]`);
            if (input) {
                input.value = info.delta;
                // Flash effect or similar could be added
            }
        }
    }

    // Update List
    const list = document.getElementById('breakdownList');
    list.innerHTML = '';

    // Update Chart
    const sortedKeys = Object.keys(data.all_probabilities).sort();
    const sortedValues = sortedKeys.map(k => data.all_probabilities[k]);

    myRadarChart.data.labels = sortedKeys;
    myRadarChart.data.datasets[0].data = sortedValues;
    myRadarChart.update();

    // Scroll to result
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}

// Demo Helper
function fillDemo(type) {
    const r1 = document.querySelector('input[name="r1"]');
    const r2 = document.querySelector('input[name="r2"]');
    const r3 = document.querySelector('input[name="r3"]');

    if (type === 'sour') {
        r1.value = 106.41;
        r2.value = 156.55;
        r3.value = 31.7;
    } else if (type === 'astringent') {
        r1.value = 40.46;
        r2.value = 95.36;
        r3.value = 95.36;
    } else if (type === 'noise') {
        r1.value = 10;
        r2.value = 15;
        r3.value = 145;
    }
}

async function testConnection() {
    const url = document.getElementById('cameraUrl').value;
    if(!url) return alert("Please enter a URL first.");
    
    try {
        const resp = await fetch('/test_connection', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({camera_url: url})
        });
        const res = await resp.json();
        if(res.status === 'success') {
            alert(`Success! Image fetched.Size: ${ res.size } `);
        } else {
            alert(`Failed: ${ res.message } `);
        }
    } catch(e) {
        alert("Error contacting server: " + e);
    }
}

console.log("Script v3 Loaded");
