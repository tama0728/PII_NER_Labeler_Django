/**
 * Project management module
 */
class ProjectManager {
    constructor() {
        this.projects = [];
        this.currentProject = null;
    }

    async loadProjects() {
        const response = await fetch('/api/projects');
        if (response.ok) {
            this.projects = await response.json();
            this.renderProjectList();
        }
    }

    async createProject(name, description) {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, description})
        });
        
        if (response.ok) {
            await this.loadProjects();
            return true;
        }
        return false;
    }

    async selectProject(projectId) {
        const response = await fetch(`/api/projects/${projectId}`);
        if (response.ok) {
            this.currentProject = await response.json();
            this.showProjectDashboard();
        }
    }

    renderProjectList() {
        const container = document.getElementById('project-list');
        container.innerHTML = this.projects.map(project => `
            <div class="project-item" onclick="projectManager.selectProject(${project.id})">
                <h3>${project.name}</h3>
                <p>${project.description || 'No description'}</p>
                <div class="project-stats">
                    <span>Tasks: ${project.task_count}</span>
                    <span>Completed: ${project.completed_task_count}</span>
                    <span>Progress: ${project.completion_percentage.toFixed(1)}%</span>
                </div>
            </div>
        `).join('');
    }

    showProjectDashboard() {
        document.getElementById('project-list-view').style.display = 'none';
        document.getElementById('project-dashboard').style.display = 'block';
        this.renderProjectDashboard();
    }

    renderProjectDashboard() {
        if (!this.currentProject) return;
        
        document.getElementById('project-name').textContent = this.currentProject.project.name;
        document.getElementById('project-description').textContent = 
            this.currentProject.project.description || 'No description';
        
        const stats = this.currentProject.statistics;
        document.getElementById('total-tasks').textContent = stats.total_tasks;
        document.getElementById('completed-tasks').textContent = stats.completed_tasks;
        document.getElementById('completion-rate').textContent = 
            `${stats.completion_percentage.toFixed(1)}%`;
    }

    backToProjectList() {
        document.getElementById('project-dashboard').style.display = 'none';
        document.getElementById('project-list-view').style.display = 'block';
        this.currentProject = null;
    }
}

window.projectManager = new ProjectManager();