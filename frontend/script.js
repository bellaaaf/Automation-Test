// frontend/script.js
// ========== Global Variables ==========
let tasks = [];
let editingTaskId = null;
let editModal = null;

// ========== Initialization ==========
document.addEventListener('DOMContentLoaded', function() {
    // Inisialisasi Bootstrap Modal
    editModal = new bootstrap.Modal(document.getElementById('editTaskModal'));
    
    // Load tasks
    loadTasks();
    
    // Event Listeners
    document.getElementById('taskForm').addEventListener('submit', handleCreateTask);
    document.getElementById('resetForm').addEventListener('click', resetForm);
    document.getElementById('refreshBtn').addEventListener('click', loadTasks);
    document.getElementById('saveEditBtn').addEventListener('click', handleUpdateTask);
});

// ========== API Functions ==========
async function fetchTasks() {
    try {
        const response = await fetch(apiUrl(API_CONFIG.ENDPOINTS.TASKS));
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching tasks:', error);
        showAlert('Gagal memuat data tugas', 'danger');
        return [];
    }
}

async function createTask(taskData) {
    try {
        const response = await fetch(apiUrl(API_CONFIG.ENDPOINTS.TASKS), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error creating task:', error);
        throw error;
    }
}

async function updateTask(id, taskData) {
    try {
        const response = await fetch(`${apiUrl(API_CONFIG.ENDPOINTS.TASKS)}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error updating task:', error);
        throw error;
    }
}

async function deleteTask(id) {
    try {
        const response = await fetch(`${apiUrl(API_CONFIG.ENDPOINTS.TASKS)}/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return true;
    } catch (error) {
        console.error('Error deleting task:', error);
        throw error;
    }
}

// ========== UI Functions ==========
async function loadTasks() {
    tasks = await fetchTasks();
    renderTasksList();
}

function renderTasksList() {
    const container = document.getElementById('tasksList');
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-clipboard-list fa-3x mb-3"></i>
                <p>Belum ada tugas. Tambahkan tugas pertama Anda!</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover">';
    html += `
        <thead>
            <tr>
                <th>ID</th>
                <th>Judul</th>
                <th>Deskripsi</th>
                <th>Status</th>
                <th>Aksi</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    tasks.forEach(task => {
        const statusBadge = getStatusBadge(task.status);
        html += `
            <tr>
                <td>${task.id}</td>
                <td><strong>${escapeHtml(task.title)}</strong></td>
                <td>${escapeHtml(task.description || '-')}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-warning me-1" onclick="openEditModal(${task.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmDelete(${task.id})" title="Hapus">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge bg-warning text-dark">Pending</span>',
        'in-progress': '<span class="badge bg-info">In Progress</span>',
        'completed': '<span class="badge bg-success">Completed</span>'
    };
    return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    document.getElementById('alertContainer').innerHTML = alertHtml;
    
    // Auto dismiss after 3 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }
    }, 3000);
}

// ========== Event Handlers ==========
async function handleCreateTask(e) {
    e.preventDefault();
    
    const taskData = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        status: document.getElementById('status').value
    };
    
    try {
        await createTask(taskData);
        showAlert('Tugas berhasil ditambahkan!', 'success');
        resetForm();
        await loadTasks();
    } catch (error) {
        showAlert('Gagal menambahkan tugas', 'danger');
    }
}

function resetForm() {
    document.getElementById('taskForm').reset();
    document.getElementById('status').value = 'pending';
}

function openEditModal(id) {
    const task = tasks.find(t => t.id === id);
    if (!task) return;
    
    editingTaskId = id;
    document.getElementById('editTaskId').value = id;
    document.getElementById('editTitle').value = task.title;
    document.getElementById('editDescription').value = task.description || '';
    document.getElementById('editStatus').value = task.status;
    
    editModal.show();
}

async function handleUpdateTask() {
    const taskData = {
        title: document.getElementById('editTitle').value,
        description: document.getElementById('editDescription').value,
        status: document.getElementById('editStatus').value
    };
    
    try {
        await updateTask(editingTaskId, taskData);
        showAlert('Tugas berhasil diperbarui!', 'success');
        editModal.hide();
        await loadTasks();
    } catch (error) {
        showAlert('Gagal memperbarui tugas', 'danger');
    }
}

async function confirmDelete(id) {
    if (confirm('Apakah Anda yakin ingin menghapus tugas ini?')) {
        try {
            await deleteTask(id);
            showAlert('Tugas berhasil dihapus!', 'success');
            await loadTasks();
        } catch (error) {
            showAlert('Gagal menghapus tugas', 'danger');
        }
    }
}