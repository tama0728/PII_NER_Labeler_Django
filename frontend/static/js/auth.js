/**
 * Authentication module
 */
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    async init() {
        await this.checkAuthStatus();
    }

    async login(username, password) {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        if (response.ok) {
            const data = await response.json();
            this.currentUser = data.user;
            this.showDashboard();
            return true;
        }
        return false;
    }

    async logout() {
        await fetch('/auth/logout', {method: 'POST'});
        this.currentUser = null;
        this.showLogin();
    }

    async checkAuthStatus() {
        // Skip authentication check for development/guest mode
        this.currentUser = {
            username: 'Guest',
            role: 'User'
        };
        this.showDashboard();
    }

    showLogin() {
        document.getElementById('login-screen').style.display = 'block';
        document.getElementById('app-screen').style.display = 'none';
    }

    showDashboard() {
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('app-screen').style.display = 'block';
        this.updateUserInfo();
    }

    updateUserInfo() {
        if (this.currentUser) {
            const userNameEl = document.getElementById('user-name');
            const userRoleEl = document.getElementById('user-role');
            
            if (userNameEl) userNameEl.textContent = this.currentUser.username;
            if (userRoleEl) userRoleEl.textContent = this.currentUser.role;
        }
    }
}

window.authManager = new AuthManager();