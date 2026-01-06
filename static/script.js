// Global variable for unigram/bigram mode
let unigram = true;

// Update button text based on mode
function updateButtonText() {
    const trainButton = document.getElementById('trainButton');
    trainButton.textContent = unigram ? 'Train Unigram Model' : 'Train Bigram Model';
}


async function getUnigramVal() {
// Sends the current JS "unigram" boolean to Flask
    await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: unigram })
    });
}


// Toggle switch handler
document.getElementById('modeToggle').addEventListener('change', async function() {
    unigram = !this.checked; // checked means Bigram in your UI
    updateButtonText();
    await getUnigramVal();
});

function showMessage(text, isError = false) {
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.className = 'message ' + (isError ? 'error' : 'success');
    setTimeout(() => msg.className = 'message', 5000);
}

document.getElementById('scrapeButton').onclick = async function() {
    this.disabled = true;
    this.textContent = 'Scraping...';
    try {
        const res = await fetch('/api/scrape', {method: 'POST'});
        const data = await res.json();
        showMessage(data.success ? data.message : data.error, !data.success);
    } catch (e) {
        showMessage('Error: ' + e.message, true);
    }
    this.disabled = false;
    this.textContent = 'Scrape Maroon 5 lyrics';
};

document.getElementById('trainButton').onclick = async function() {
    this.disabled = true;
    this.textContent = 'Training...';
    try {
        getUnigramVal()
        const res = await fetch('/api/train', {method: 'POST'});
        const data = await res.json();
        showMessage(data.success ? data.message : data.error, !data.success);
    } catch (e) {
        showMessage('Error: ' + e.message, true);
    }
    this.disabled = false;
    this.textContent = updateButtonText();
    ;
};

document.getElementById('generateButton').onclick = async function() {
    this.disabled = true;
    this.textContent = 'Generating...';
    try {
        getUnigramVal()
        const res = await fetch('/api/generate', {method: 'POST'});
        const data = await res.json();
        if (data.success) {
            const content = document.getElementById('songContent');
            content.innerHTML = data.song.split('\n').map(line => 
                `<div class="song-line">${line}</div>`
            ).join('');
            document.getElementById('songDisplay').classList.add('show');
            showMessage('Song generated!');
        } else {
            showMessage('Train the corresponding model first', true);
        }
    } catch (e) {
        showMessage('Error: ' + e.message, true);
    }
    this.disabled = false;
    this.textContent = 'Generate Song';
};