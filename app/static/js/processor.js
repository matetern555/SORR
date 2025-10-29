// Funkcja rozpoczynająca pełny pipeline przetwarzania
async function startProcessing(audioId) {
    // Ukryj sekcję uploadu, pokaż sekcję przetwarzania
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('processing-section').style.display = 'block';
    
    let transcriptionId = null;
    
    try {
        // KROK 1: Transkrypcja
        updateStepStatus('transcription', 'processing', 'Przetwarzanie...');
        updateProgress(10);
        
        const transcriptionResponse = await fetch(`/api/transcription/transcribe/${audioId}`, {
            method: 'POST'
        });
        
        if (!transcriptionResponse.ok) {
            const error = await transcriptionResponse.json();
            throw new Error(error.detail || 'Błąd podczas transkrypcji');
        }
        
        const transcription = await transcriptionResponse.json();
        transcriptionId = transcription.id;
        
        updateStepStatus('transcription', 'completed', '✅ Zakończono');
        updateProgress(33);
        
        // KROK 2: Diarization
        updateStepStatus('diarization', 'processing', 'Przetwarzanie...');
        
        const diarizationResponse = await fetch(`/api/diarization/analyze/${transcriptionId}`, {
            method: 'POST'
        });
        
        if (!diarizationResponse.ok) {
            const error = await diarizationResponse.json();
            throw new Error(error.detail || 'Błąd podczas diaryzacji');
        }
        
        await diarizationResponse.json();
        updateStepStatus('diarization', 'completed', '✅ Zakończono');
        updateProgress(66);
        
        // KROK 3: Ocena
        updateStepStatus('evaluation', 'processing', 'Przetwarzanie...');
        
        const evaluationResponse = await fetch(`/api/evaluation/evaluate/${transcriptionId}?scorecard_type=SERVICE`, {
            method: 'POST'
        });
        
        if (!evaluationResponse.ok) {
            const error = await evaluationResponse.json();
            throw new Error(error.detail || 'Błąd podczas oceny');
        }
        
        await evaluationResponse.json();
        updateStepStatus('evaluation', 'completed', '✅ Zakończono');
        updateProgress(100);
        
        // Pokazuj przyciski wyników
        showResultsSection(transcriptionId);
        
    } catch (error) {
        console.error('Błąd podczas przetwarzania:', error);
        alert('Błąd: ' + error.message);
        updateStepStatus('evaluation', 'error', '❌ Błąd: ' + error.message);
    }
}

function updateStepStatus(stepName, status, message) {
    const step = document.getElementById(`step-${stepName}`);
    const statusEl = document.getElementById(`status-${stepName}`);
    
    if (step && statusEl) {
        statusEl.textContent = message;
        step.classList.remove('pending', 'processing', 'completed', 'error');
        step.classList.add(status);
    }
}

function updateProgress(percent) {
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
}

function showResultsSection(transcriptionId) {
    document.getElementById('processing-section').style.display = 'none';
    document.getElementById('history-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    
    // Przypisz event listeners do przycisków
    document.getElementById('show-transcription').onclick = () => {
        window.showTranscription(transcriptionId);
    };
    
    document.getElementById('show-diarization').onclick = () => {
        window.showDiarization(transcriptionId);
    };
    
    document.getElementById('show-evaluation').onclick = () => {
        window.showEvaluation(transcriptionId);
    };
}

// Funkcje globalne do wyświetlania wyników
window.showTranscription = async function(transcriptionId) {
    try {
        const response = await fetch(`/api/transcription/transcriptions/${transcriptionId}`);
        if (!response.ok) throw new Error('Błąd pobierania transkrypcji');
        
        const data = await response.json();
        document.getElementById('transcription-text').textContent = data.text || 'Brak transkrypcji';
        const view = document.getElementById('transcription-view');
        view.style.display = 'block';
        // Przewiń do widoku transkrypcji
        view.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        alert('Błąd: ' + error.message);
    }
}

window.showDiarization = async function(transcriptionId) {
    try {
        const response = await fetch(`/api/diarization/segments/${transcriptionId}`);
        if (!response.ok) throw new Error('Błąd pobierania diaryzacji');
        
        const segments = await response.json();
        
        const html = segments.map(s => 
            `<div class="segment">
                <strong>${s.speaker_label || 'Nieznany'}</strong> 
                [${formatTime(s.start_time)}]: ${s.text || ''}
            </div>`
        ).join('');
        
        document.getElementById('diarization-segments').innerHTML = html;
        const view = document.getElementById('diarization-view');
        view.style.display = 'block';
        // Przewiń do widoku diaryzacji
        view.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        alert('Błąd: ' + error.message);
    }
}

window.showEvaluation = async function(transcriptionId) {
    try {
        const response = await fetch(`/api/evaluation/evaluations/${transcriptionId}`);
        if (!response.ok) throw new Error('Błąd pobierania oceny');
        
        const evaluation = await response.json();
        
        // Renderuj ocenę
        let html = `
            <div class="score-display">
                <h4>Wynik ogólny: ${evaluation.overall_score}%</h4>
                <p><strong>Ocena:</strong> ${evaluation.grade || 'N/A'}</p>
                <p><strong>Komentarz:</strong></p>
                <p>${evaluation.final_comment || 'Brak komentarza'}</p>
            </div>
        `;
        
        // Jeśli są kategorie, dodaj je (z deduplikacją)
        if (evaluation.category_scores && evaluation.category_scores.length > 0) {
            // Usuń duplikaty kategorii (po nazwie)
            const uniqueCategories = [];
            const seenNames = new Set();
            
            for (const cat of evaluation.category_scores) {
                if (!seenNames.has(cat.category_name)) {
                    seenNames.add(cat.category_name);
                    uniqueCategories.push(cat);
                }
            }
            
            html += '<h4>Kategorie:</h4><ul>';
            uniqueCategories.forEach(cat => {
                html += `<li class="category-item">
                    <strong>${cat.category_name}</strong>: ${cat.score}/5 (${cat.points} pkt)
                    <p class="category-comment">${cat.comment || ''}</p>`;
                
                // Wyświetl cytaty jeśli są dostępne
                if (cat.quotes && cat.quotes.length > 0) {
                    html += '<div class="quotes-section"><strong>Dowody:</strong><ul class="quotes-list">';
                    cat.quotes.forEach(quote => {
                        const quoteIcon = quote.is_positive ? '✅' : '❌';
                        const timestamp = quote.timestamp ? ` [${quote.timestamp}]` : '';
                        html += `<li class="quote-item">
                            <span class="quote-icon">${quoteIcon}</span>
                            <strong>${quote.speaker}</strong>${timestamp}: "${quote.text}"
                        </li>`;
                    });
                    html += '</ul></div>';
                }
                
                html += '</li>';
            });
            html += '</ul>';
        }
        
        document.getElementById('evaluation-results').innerHTML = html;
        const view = document.getElementById('evaluation-view');
        view.style.display = 'block';
        // Przewiń do widoku oceny
        view.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        alert('Błąd: ' + error.message);
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

