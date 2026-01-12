export class AuthRepository {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:8000';
    }

    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Login failed");
        }

        return await response.json(); // Returns {access_token: "...", token_type: "bearer"}
    }
}