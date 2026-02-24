const runBtn = document.getElementById('runBtn');
const logsDiv = document.getElementById('logs');
const resultContainer = document.getElementById('resultContainer');
const loader = document.getElementById('loader');

// Elements to update
const resImage = document.getElementById('resultImage');
const resCaption = document.getElementById('resultCaption');
const resCritique = document.getElementById('resultCritique');
const resResearch = document.getElementById('resultResearch');

let isRunning = false;

runBtn.addEventListener('click', async () => {
    if (isRunning) return;

    isRunning = true;
    runBtn.classList.add('disabled');
    runBtn.innerText = "EXECUTING...";

    // Reset UI
    logsDiv.innerHTML = '<div class="log-line">Initializing Command...</div>';
    resultContainer.classList.add('hidden');
    loader.classList.add('active');

    try {
        // Trigger Start
        await fetch('/api/run', { method: 'POST', body: JSON.stringify({}) });

        // Start Polling
        pollStatus();
    } catch (e) {
        log(`Error: ${e}`);
        isRunning = false;
    }
});

function log(msg) {
    const div = document.createElement('div');
    div.className = 'log-line new';
    div.innerText = `> ${msg}`;
    logsDiv.appendChild(div);
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

async function pollStatus() {
    const interval = setInterval(async () => {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();

            // Sync Logs
            if (data.logs.length > logsDiv.childElementCount) {
                // Determine new logs
                const newLogs = data.logs.slice(logsDiv.childElementCount);
                newLogs.forEach(l => log(l));
            }

            if (data.status === 'completed' || data.status === 'error') {
                clearInterval(interval);
                finish(data);
            }
        } catch (e) {
            console.error(e);
        }
    }, 1000);
}

function finish(data) {
    isRunning = false;
    runBtn.classList.remove('disabled');
    runBtn.innerText = "INITIALIZE WORKFLOW";
    loader.classList.remove('active');

    if (data.status === 'completed' && data.result) {
        // Populate Result
        resImage.src = data.result.image;
        resCaption.innerText = data.result.caption;
        resCritique.innerText = data.result.critique || "N/A";
        resResearch.innerText = data.result.research ? data.result.research.substring(0, 100) + "..." : "No data";

        resultContainer.classList.remove('hidden');
    }
}
