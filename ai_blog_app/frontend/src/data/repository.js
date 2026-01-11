export class DecisionRepository {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:8000';
    }

    async fetchDecision() {
        try {
            const response = await fetch(`${this.baseUrl}/decision`);
            if (!response.ok) throw new Error("Backend unreachable");
            return await response.json();
        } catch (error) {
            console.error("Repository Error:", error);
            throw error;
        }
    }
}