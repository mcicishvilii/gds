import { DecisionRepository } from './data/repository.js';

const repo = new DecisionRepository();

// UI References
const btn = document.getElementById('decideBtn');
const resultDiv = document.getElementById('result');
const answerText = document.getElementById('answerText');
const answerImage = document.getElementById('answerImage');

async function handleDecisionRequest() {
    // State management: Loading
    btn.innerText = "Consulting the Oracle...";
    btn.disabled = true;

    try {
        const decision = await repo.fetchDecision();
        
        // Update View
        answerText.innerText = decision.answer;
        answerImage.src = decision.image;
        resultDiv.classList.remove('hidden');
    } catch (error) {
        alert("Check if the Python Backend is running at :8000");
    } finally {
        btn.innerText = "Ask Again";
        btn.disabled = false;
    }
}

btn.addEventListener('click', handleDecisionRequest);