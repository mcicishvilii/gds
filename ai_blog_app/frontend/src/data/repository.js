export class DecisionRepository {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:8000';
    }

    async fetchDecision() {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.baseUrl}/decision`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.status === 401) throw { status: 401 };
        return await response.json();
    }
}