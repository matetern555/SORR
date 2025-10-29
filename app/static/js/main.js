// Upload audio
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('audio-file');
const fileName = document.getElementById('file-name');
const processBtn = document.getElementById('process-btn');

let currentAudioId = null;

// Drag & drop
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', async (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) await uploadFile(file);
});

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) await uploadFile(file);
});

async function uploadFile(file) {
    // Sprawdź czy to plik audio
    if (!file.type.startsWith('audio/')) {
        alert('Proszę wybrać plik audio!');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        fileName.textContent = `⏳ Przesyłanie...`;
        fileName.style.display = 'block';
        processBtn.disabled = true;
        
        const response = await fetch('/api/audio/upload/', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd podczas uploadu');
        }
        
        const audio = await response.json();
        currentAudioId = audio.id;
        
        fileName.textContent = `✅ ${audio.filename}`;
        fileName.style.display = 'block';
        processBtn.style.display = 'block';
        processBtn.disabled = false;
        
        console.log('Upload zakończony, audio_id:', currentAudioId);
        
    } catch (error) {
        console.error('Błąd podczas uploadu:', error);
        alert('Błąd podczas uploadu: ' + error.message);
        fileName.style.display = 'none';
        processBtn.style.display = 'none';
    }
}

// Przycisk rozpoczynający analizę
processBtn.addEventListener('click', async () => {
    if (currentAudioId) {
        if (typeof startProcessing === 'function') {
            await startProcessing(currentAudioId);
            // Po zakończeniu odśwież historię
            setTimeout(() => loadConversationsHistory(), 1000);
        } else {
            console.error('Funkcja startProcessing nie jest dostępna!');
            alert('Błąd: Funkcja przetwarzania nie jest dostępna. Odśwież stronę.');
        }
    }
});

// Ładowanie historii rozmów
async function loadConversationsHistory() {
    const listContainer = document.getElementById('conversations-list');
    
    try {
        const response = await fetch('/api/evaluation/conversations/history');
        if (!response.ok) {
            throw new Error('Błąd pobierania historii');
        }
        
        const conversations = await response.json();
        
        if (conversations.length === 0) {
            listContainer.innerHTML = '<p style="color: #666; text-align: center;">Brak zapisanych rozmów</p>';
            return;
        }
        
        const html = conversations.map(conv => {
            const date = new Date(conv.audio_created_at);
            const dateStr = date.toLocaleString('pl-PL');
            
            const hasEvaluation = conv.evaluation_id !== null;
            const scoreText = hasEvaluation 
                ? `${conv.evaluation_score?.toFixed(1)}% (${conv.evaluation_grade})`
                : 'Brak oceny';
            
            return `
                <div class="conversation-item" onclick="loadConversation(${conv.transcription_id})">
                    <div class="conversation-header">
                        <div class="conversation-filename">${conv.audio_filename}</div>
                        <div class="conversation-date">${dateStr}</div>
                    </div>
                    <div class="conversation-status">
                        <span>
                            <span class="status-badge completed">✅ Transkrypcja</span>
                        </span>
                        ${hasEvaluation ? '<span><span class="status-badge completed">✅ Ocena</span></span>' : '<span><span class="status-badge pending">⏳ Brak oceny</span></span>'}
                    </div>
                    ${hasEvaluation ? `<div class="conversation-score has-score">Wynik: ${scoreText}</div>` : '<div class="conversation-score no-score">Oczekiwanie na ocenę</div>'}
                </div>
            `;
        }).join('');
        
        listContainer.innerHTML = html;
        
    } catch (error) {
        console.error('Błąd podczas ładowania historii:', error);
        listContainer.innerHTML = '<p style="color: #dc3545;">Błąd podczas ładowania historii rozmów</p>';
    }
}

// Funkcja do ładowania wybranej rozmowy (globalna)
window.loadConversation = async function(transcriptionId) {
    // Ukryj sekcję uploadu i pokaż sekcję wyników
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('history-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    
    // Przewiń do sekcji wyników
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Poczekaj na załadowanie funkcji z processor.js
    if (typeof showTranscription === 'function' && typeof showDiarization === 'function' && typeof showEvaluation === 'function') {
        // Przypisz event listeners do przycisków
        document.getElementById('show-transcription').onclick = () => {
            showTranscription(transcriptionId);
        };
        
        document.getElementById('show-diarization').onclick = () => {
            showDiarization(transcriptionId);
        };
        
        document.getElementById('show-evaluation').onclick = () => {
            showEvaluation(transcriptionId);
        };
    } else {
        // Jeśli funkcje jeszcze nie są załadowane, poczekaj
        setTimeout(() => {
            if (typeof showTranscription === 'function') {
                document.getElementById('show-transcription').onclick = () => showTranscription(transcriptionId);
            }
            if (typeof showDiarization === 'function') {
                document.getElementById('show-diarization').onclick = () => showDiarization(transcriptionId);
            }
            if (typeof showEvaluation === 'function') {
                document.getElementById('show-evaluation').onclick = () => showEvaluation(transcriptionId);
            }
        }, 100);
    }
}

// Funkcja powrotu do historii (globalna)
window.showHistory = function() {
    document.getElementById('upload-section').style.display = 'block';
    document.getElementById('history-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('transcription-view').style.display = 'none';
    document.getElementById('diarization-view').style.display = 'none';
    document.getElementById('evaluation-view').style.display = 'none';
    document.getElementById('history-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Załaduj historię przy starcie strony
document.addEventListener('DOMContentLoaded', () => {
    loadConversationsHistory();
});

