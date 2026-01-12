import { DecisionRepository } from './data/repository.js';
import { AuthRepository } from './data/authRepository.js';

const decisionRepo = new DecisionRepository();
const authRepo = new AuthRepository();

function showPage(pageId) {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('oraclePage').classList.add('hidden');
    
    const page = document.getElementById(pageId);
    if (page) page.classList.remove('hidden');
}

function navigate() {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('username');

    if (!token) {
        showPage('loginPage');
        const loginBtn = document.getElementById('loginBtn');
        loginBtn.onclick = async () => {
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            try {
                const data = await authRepo.login(u, p);
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('username', data.username || u);
                navigate(); 
            } catch (e) {
                alert("Login failed: " + e.message);
            }
        };
    } else {
        showPage('oraclePage');
        document.getElementById('userGreeting').innerText = `Oracle Access: ${user}`;
        
        document.getElementById('decideBtn').onclick = async () => {
            const resDiv = document.getElementById('result');
            try {
                const d = await decisionRepo.fetchDecision();
                document.getElementById('answerText').innerText = d.answer;
                document.getElementById('answerImage').src = d.image;
                resDiv.classList.remove('hidden');
            } catch (e) { alert("Session expired"); localStorage.clear(); navigate(); }
        };

        document.getElementById('logoutBtn').onclick = () => {
            localStorage.clear();
            navigate();
        };
    }
}
window.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");
    navigate();
});