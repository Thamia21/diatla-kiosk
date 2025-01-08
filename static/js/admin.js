// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Sidebar toggle
    document.getElementById('sidebarCollapse').addEventListener('click', function() {
        document.getElementById('sidebar').classList.toggle('active');
    });

    // Navigation
    const navLinks = document.querySelectorAll('[data-page]');
    const contentPages = document.querySelectorAll('.content-page');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and pages
            navLinks.forEach(l => l.parentElement.classList.remove('active'));
            contentPages.forEach(page => page.classList.remove('active'));
            
            // Add active class to clicked link and corresponding page
            this.parentElement.classList.add('active');
            document.getElementById(`${this.dataset.page}-page`).classList.add('active');

            // Load data for the selected page
            if (this.dataset.page === 'orders') {
                loadRecentOrders();
            } else if (this.dataset.page === 'dashboard') {
                loadDashboardData();
                loadRecentOrders();
            } else if (this.dataset.page === 'menu') {
                loadMenuItems();
            }
        });
    });

    // Load initial data
    loadDashboardData();
    loadRecentOrders();
    loadMenuItems();
    
    // Auto-refresh orders every 30 seconds
    setInterval(() => {
        if (document.getElementById('orders-page').classList.contains('active') ||
            document.getElementById('dashboard-page').classList.contains('active')) {
            loadRecentOrders();
        }
    }, 30000);

    // Add event listeners for order filters
    const statusFilter = document.querySelector('#order-status-filter');
    const dateFilter = document.querySelector('#order-date-filter');
    const searchFilter = document.querySelector('#order-search-filter');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            loadOrders();
        });
    }
    
    if (dateFilter) {
        dateFilter.addEventListener('change', () => {
            loadOrders();
        });
    }
    
    if (searchFilter) {
        searchFilter.addEventListener('input', debounce(() => {
            loadOrders();
        }, 300));
    }
    
    // Initial load of all orders
    loadOrders();
});

// Menu Item Modal
let menuItemModal = null;
let currentMenuItemId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the menu item modal
    menuItemModal = new bootstrap.Modal(document.getElementById('menuItemModal'));
    
    // Add New Item button click handler
    document.getElementById('add-menu-item').addEventListener('click', () => {
        currentMenuItemId = null;
        clearMenuItemForm();
        loadCategories();
        document.querySelector('#menuItemModal .modal-title').textContent = 'Add New Item';
        menuItemModal.show();
    });
    
    // Save menu item button click handler
    document.getElementById('save-menu-item').addEventListener('click', saveMenuItem);
    
    // Image source type radio buttons handler
    document.querySelectorAll('input[name="imageSourceType"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const fileGroup = document.getElementById('fileInputGroup');
            const urlGroup = document.getElementById('urlInputGroup');
            
            if (e.target.value === 'file') {
                fileGroup.style.display = 'block';
                urlGroup.style.display = 'none';
            } else {
                fileGroup.style.display = 'none';
                urlGroup.style.display = 'block';
            }
        });
    });
});

// Clear menu item form
function clearMenuItemForm() {
    document.getElementById('item-name').value = '';
    document.getElementById('item-category').value = '';
    document.getElementById('item-price').value = '';
    document.getElementById('item-description').value = '';
    document.getElementById('item-image').value = '';
    document.getElementById('item-image-url').value = '';
    document.getElementById('item-available').checked = true;
    document.getElementById('imageSourceFile').checked = true;
    document.getElementById('fileInputGroup').style.display = 'block';
    document.getElementById('urlInputGroup').style.display = 'none';
}

// Load categories for the dropdown
async function loadCategories() {
    try {
        const response = await fetch('/api/admin/categories');
        if (!response.ok) {
            throw new Error('Failed to load categories');
        }
        const categories = await response.json();
        
        const select = document.getElementById('item-category');
        select.innerHTML = '<option value="">Select Category</option>';
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading categories:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to load categories'
        });
    }
}

// Save menu item
async function saveMenuItem() {
    try {
        const form = document.getElementById('menu-item-form');
        const formData = new FormData();
        
        // Get form values
        const name = document.getElementById('item-name').value;
        const category = document.getElementById('item-category').value;
        const price = document.getElementById('item-price').value;
        const description = document.getElementById('item-description').value;
        const available = document.getElementById('item-available').checked;
        const imageSourceType = document.querySelector('input[name="imageSourceType"]:checked').value;
        
        // Validate required fields
        if (!name || !category || !price) {
            Swal.fire({
                icon: 'warning',
                title: 'Missing Information',
                text: 'Please fill in all required fields'
            });
            return;
        }
        
        // Add form data
        formData.append('name', name);
        formData.append('category', category);
        formData.append('price', price);
        formData.append('description', description);
        formData.append('available', available);
        
        // Handle image based on source type
        if (imageSourceType === 'file') {
            const imageFile = document.getElementById('item-image').files[0];
            if (imageFile) {
                formData.append('image', imageFile);
            }
        } else {
            const imageUrl = document.getElementById('item-image-url').value;
            if (imageUrl) {
                formData.append('image_url', imageUrl);
            }
        }
        
        // Add menu item ID if editing
        if (currentMenuItemId) {
            formData.append('id', currentMenuItemId);
        }
        
        // Show loading state
        const saveButton = document.getElementById('save-menu-item');
        saveButton.disabled = true;
        saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        
        // Send request
        const url = currentMenuItemId ? 
            `/api/admin/menu-items/${currentMenuItemId}` : 
            '/api/admin/menu-items';
            
        const response = await fetch(url, {
            method: currentMenuItemId ? 'PUT' : 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to save menu item');
        }
        
        const result = await response.json();
        
        // Hide modal and refresh menu items
        menuItemModal.hide();
        loadMenuItems();
        
        // Show success message
        Swal.fire({
            icon: 'success',
            title: 'Success',
            text: currentMenuItemId ? 'Menu item updated successfully' : 'Menu item added successfully',
            timer: 2000,
            showConfirmButton: false
        });
        
    } catch (error) {
        console.error('Error saving menu item:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to save menu item'
        });
    } finally {
        // Reset button state
        const saveButton = document.getElementById('save-menu-item');
        saveButton.disabled = false;
        saveButton.textContent = 'Save';
    }
}

// Edit menu item
async function editMenuItem(id) {
    try {
        const response = await fetch(`/api/admin/menu-items/${id}`);
        if (!response.ok) {
            throw new Error('Failed to load menu item');
        }
        const item = await response.json();
        
        // Set current item ID
        currentMenuItemId = id;
        
        // Load categories and wait for them to load
        await loadCategories();
        
        // Fill form with item data
        document.getElementById('item-name').value = item.name;
        document.getElementById('item-category').value = item.category.id;
        document.getElementById('item-price').value = item.price;
        document.getElementById('item-description').value = item.description || '';
        document.getElementById('item-available').checked = item.available;
        
        // Handle image URL
        if (item.image_url) {
            if (item.image_url.startsWith('/static/uploads/')) {
                // It's an uploaded file
                document.getElementById('imageSourceFile').checked = true;
                document.getElementById('fileInputGroup').style.display = 'block';
                document.getElementById('urlInputGroup').style.display = 'none';
            } else {
                // It's an external URL
                document.getElementById('imageSourceUrl').checked = true;
                document.getElementById('item-image-url').value = item.image_url;
                document.getElementById('fileInputGroup').style.display = 'none';
                document.getElementById('urlInputGroup').style.display = 'block';
            }
        }
        
        // Update modal title
        document.querySelector('#menuItemModal .modal-title').textContent = 'Edit Menu Item';
        
        // Show modal
        menuItemModal.show();
        
    } catch (error) {
        console.error('Error loading menu item:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to load menu item'
        });
    }
}

// Dashboard Data
async function loadDashboardData() {
    try {
        const response = await fetch('/api/admin/dashboard');
        if (!response.ok) {
            throw new Error('Failed to load dashboard data');
        }
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update statistics with proper formatting
        document.getElementById('today-orders').textContent = data.todayOrders || 0;
        document.getElementById('today-revenue').textContent = `R${(data.todayRevenue || 0).toFixed(2)}`;
        document.getElementById('total-items').textContent = data.totalItems || 0;
        document.getElementById('total-categories').textContent = data.totalCategories || 0;
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Set default values if there's an error
        document.getElementById('today-orders').textContent = '0';
        document.getElementById('today-revenue').textContent = 'R0.00';
        document.getElementById('total-items').textContent = '0';
        document.getElementById('total-categories').textContent = '0';
        
        showError('Failed to load dashboard data');
    }
}

// Recent Orders
async function loadRecentOrders() {
    try {
        console.log('Loading recent orders...');
        const response = await fetch('/api/admin/recent-orders');
        if (!response.ok) {
            throw new Error('Failed to load recent orders');
        }
        const orders = await response.json();
        console.log('Received orders:', orders);
        
        const tbody = document.querySelector('#recent-orders-table tbody');
        if (!tbody) {
            console.error('Orders table not found');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (!orders || orders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">No orders found</td>
                </tr>
            `;
            return;
        }
        
        orders.forEach(order => {
            const tr = document.createElement('tr');
            const orderDate = new Date(order.created_at);
            const formattedDate = orderDate.toLocaleString('en-ZA', {
                year: 'numeric',
                month: 'numeric',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
            
            tr.innerHTML = `
                <td>${order.order_number || order.id}</td>
                <td>${formattedDate}</td>
                <td>${order.customer}</td>
                <td>${order.items}</td>
                <td>R${parseFloat(order.total).toFixed(2)}</td>
                <td>
                    <span class="badge ${order.status === 'paid' ? 'paid' : 'pending'}">${order.status}</span>
                </td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn-action view" onclick="viewOrder(${order.id})" title="View Order">
                            <i class="bx bx-show"></i>
                        </button>
                        ${order.status === 'pending' ? `
                            <button type="button" class="btn-action approve" onclick="processOrder(${order.id})" title="Process Order">
                                <i class="bx bx-check"></i>
                            </button>
                            <button type="button" class="btn-action reject" onclick="cancelOrder(${order.id})" title="Cancel Order">
                                <i class="bx bx-x"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
    } catch (error) {
        console.error('Error loading recent orders:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to load recent orders'
        });
    }
}

// Load orders with filters
async function loadOrders() {
    try {
        const statusFilter = document.querySelector('#order-status-filter');
        const dateFilter = document.querySelector('#order-date-filter');
        const searchFilter = document.querySelector('#order-search-filter');

        // Build query parameters
        const params = new URLSearchParams();
        if (statusFilter && statusFilter.value !== 'all') {
            params.append('status', statusFilter.value);
        }
        if (dateFilter && dateFilter.value) {
            params.append('date', dateFilter.value);
        }
        if (searchFilter && searchFilter.value) {
            params.append('search', searchFilter.value);
        }

        console.log('Fetching orders with params:', params.toString());
        const response = await fetch(`/api/admin/orders?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to load orders');
        }
        const orders = await response.json();
        console.log('Received orders:', orders);
        
        const ordersTableBody = document.querySelector('#orders-page tbody');
        if (!ordersTableBody) {
            console.error('Orders table body not found');
            return;
        }
        
        ordersTableBody.innerHTML = '';
        
        if (orders.length === 0) {
            ordersTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">No orders found</td>
                </tr>
            `;
            return;
        }
        
        orders.forEach(order => {
            console.log('Processing order:', order);
            // Format the date
            const orderDate = new Date(order.created_at);
            const formattedDate = orderDate.toLocaleString('en-ZA', {
                year: 'numeric',
                month: 'numeric',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });

            // Ensure items is a string
            const itemsDisplay = typeof order.items === 'string' ? order.items : 'No items';

            const row = `
                <tr>
                    <td>${order.order_number}</td>
                    <td>${formattedDate}</td>
                    <td>${order.customer}</td>
                    <td>${itemsDisplay}</td>
                    <td>R${order.total.toFixed(2)}</td>
                    <td><span class="badge ${order.status === 'paid' ? 'paid' : 'pending'}">${order.status}</span></td>
                    <td>
                        <button class="btn-action view" onclick="viewOrder(${order.id})">View</button>
                        ${order.status === 'pending' ? `
                            <button class="btn-action approve" onclick="processOrder(${order.id})">Process</button>
                            <button class="btn-action reject" onclick="cancelOrder(${order.id})">Cancel</button>
                        ` : ''}
                    </td>
                </tr>
            `;
            ordersTableBody.innerHTML += row;
        });
    } catch (error) {
        console.error('Error loading orders:', error);
        showError('Failed to load orders. Please try again.');
    }
}

// Load initial orders when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Loading initial orders');
    loadOrders();
    
    // Set up filter event listeners
    const statusFilter = document.querySelector('#order-status-filter');
    const dateFilter = document.querySelector('#order-date-filter');
    const searchFilter = document.querySelector('#order-search-filter');

    if (statusFilter) {
        statusFilter.addEventListener('change', loadOrders);
    }
    if (dateFilter) {
        dateFilter.addEventListener('change', loadOrders);
    }
    if (searchFilter) {
        let debounceTimer;
        searchFilter.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadOrders, 300);
        });
    }
    
    // Refresh orders every 30 seconds
    setInterval(loadOrders, 30000);
});

// View order details
async function viewOrder(orderId) {
    try {
        const response = await fetch(`/api/order/${orderId}`);
        if (!response.ok) {
            throw new Error('Failed to load order details');
        }
        const orderResponse = await response.json();
        if (!orderResponse.success) {
            throw new Error(orderResponse.message || 'Failed to load order details');
        }
        const order = orderResponse.order;
        
        // Create and show modal with order details
        const modalHtml = `
            <div class="modal fade" id="orderDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Order Details #${order.order_number}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="order-info mb-3">
                                <p><strong>Customer:</strong> ${order.customer_name}</p>
                                <p><strong>Email:</strong> ${order.customer_email}</p>
                                <p><strong>Phone:</strong> ${order.customer_phone}</p>
                                <p><strong>Status:</strong> <span class="badge ${order.status === 'paid' ? 'paid' : 'pending'}">${order.status}</span></p>
                                <p><strong>Date:</strong> ${new Date(order.created_at).toLocaleString()}</p>
                                ${order.special_instructions ? `
                                    <p><strong>Special Instructions:</strong> ${order.special_instructions}</p>
                                ` : ''}
                            </div>
                            <div class="order-items">
                                <h6>Order Items</h6>
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Item</th>
                                            <th>Quantity</th>
                                            <th>Price</th>
                                            <th>Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${order.items.map(item => `
                                            <tr>
                                                <td>${item.name}</td>
                                                <td>${item.quantity}</td>
                                                <td>R${item.price.toFixed(2)}</td>
                                                <td>R${(item.price * item.quantity).toFixed(2)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                    <tfoot>
                                        <tr>
                                            <th colspan="3">Total</th>
                                            <th>R${order.total_amount.toFixed(2)}</th>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            ${order.status === 'pending' ? `
                                <button type="button" class="btn-action approve process-order" data-order-id="${order.id}">
                                    Process Order
                                </button>
                                <button type="button" class="btn-action reject cancel-order" data-order-id="${order.id}">
                                    Cancel Order
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('orderDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to document
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Initialize and show modal
        const modal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
        modal.show();
        
        // Add event listeners for action buttons in modal
        const modalProcessBtn = document.querySelector('#orderDetailsModal .process-order');
        if (modalProcessBtn) {
            modalProcessBtn.addEventListener('click', () => {
                processOrder(orderId);
                modal.hide();
            });
        }
        
        const modalCancelBtn = document.querySelector('#orderDetailsModal .cancel-order');
        if (modalCancelBtn) {
            modalCancelBtn.addEventListener('click', () => {
                cancelOrder(orderId);
                modal.hide();
            });
        }
        
    } catch (error) {
        console.error('Error loading order details:', error);
        showError('Failed to load order details');
    }
}

// Process order
async function processOrder(orderId) {
    try {
        const response = await fetch(`/api/order/${orderId}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Failed to process order');
        }
        
        // Show success message
        Swal.fire({
            icon: 'success',
            title: 'Order Processed',
            text: data.message,
            showConfirmButton: false,
            timer: 1500
        });
        
        // Reload orders
        loadRecentOrders();
        loadDashboardData();
        
    } catch (error) {
        console.error('Error processing order:', error);
        showError(error.message || 'Failed to process order');
    }
}

// Cancel order
async function cancelOrder(orderId) {
    try {
        // Ask for confirmation
        const result = await Swal.fire({
            icon: 'warning',
            title: 'Cancel Order',
            text: 'Are you sure you want to cancel this order?',
            showCancelButton: true,
            confirmButtonText: 'Yes, cancel it',
            cancelButtonText: 'No, keep it'
        });
        
        if (result.isConfirmed) {
            const response = await fetch(`/api/order/${orderId}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to cancel order');
            }
            
            // Show success message
            Swal.fire({
                icon: 'success',
                title: 'Order Cancelled',
                text: data.message,
                showConfirmButton: false,
                timer: 1500
            });
            
            // Reload orders
            loadRecentOrders();
            loadDashboardData();
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        showError('Failed to cancel order');
    }
}

// Load menu items
async function loadMenuItems() {
    try {
        const response = await fetch('/api/admin/menu-items');
        if (!response.ok) {
            throw new Error('Failed to load menu items');
        }
        const items = await response.json();
        
        const tbody = document.querySelector('#menu-items-table tbody');
        if (!tbody) {
            console.error('Menu items table not found');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">No menu items found</td>
                </tr>
            `;
            return;
        }
        
        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-center">
                    ${item.image_url ? `
                        <img src="${item.image_url}" alt="${item.name}" class="menu-item-image rounded" width="60" height="60" style="object-fit: cover;">
                    ` : '<div class="no-image">No Image</div>'}
                </td>
                <td class="align-middle">${item.name}</td>
                <td class="align-middle">${item.description || 'No description'}</td>
                <td class="align-middle">${item.category.name}</td>
                <td class="align-middle">R${item.price.toFixed(2)}</td>
                <td class="align-middle">
                    <span class="badge bg-${item.available ? 'success' : 'danger'}">
                        ${item.available ? 'Available' : 'Not Available'}
                    </span>
                </td>
                <td class="align-middle">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-primary" onclick="editMenuItem(${item.id})" title="Edit Item">
                            <i class="bx bx-edit"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-${item.available ? 'warning' : 'success'}" 
                                onclick="toggleMenuItemAvailability(${item.id})" 
                                title="${item.available ? 'Mark as Unavailable' : 'Mark as Available'}">
                            <i class="bx bx-${item.available ? 'x' : 'check'}"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-danger" onclick="deleteMenuItem(${item.id})" title="Delete Item">
                            <i class="bx bx-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
    } catch (error) {
        console.error('Error loading menu items:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to load menu items'
        });
    }
}

// Toggle menu item availability
async function toggleMenuItemAvailability(itemId) {
    try {
        const response = await fetch(`/api/admin/menu-items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ available: !item.available })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update menu item');
        }
        
        // Reload menu items
        loadMenuItems();
        
    } catch (error) {
        console.error('Error updating menu item:', error);
        showError('Failed to update menu item');
    }
}

// Delete menu item
async function deleteMenuItem(itemId) {
    try {
        const result = await Swal.fire({
            title: 'Delete Menu Item',
            text: 'Are you sure you want to delete this menu item?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it',
            cancelButtonText: 'No, keep it'
        });
        
        if (result.isConfirmed) {
            const response = await fetch(`/api/admin/menu-items/${itemId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete menu item');
            }
            
            // Show success message
            Swal.fire({
                icon: 'success',
                title: 'Menu Item Deleted',
                showConfirmButton: false,
                timer: 1500
            });
            
            // Reload menu items
            loadMenuItems();
        }
    } catch (error) {
        console.error('Error deleting menu item:', error);
        showError('Failed to delete menu item');
    }
}

// Add menu item form handler
const addMenuItemForm = document.getElementById('addMenuItemForm');
if (addMenuItemForm) {
    addMenuItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const formData = new FormData(addMenuItemForm);
            
            const response = await fetch('/api/admin/menu-items', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to add menu item');
            }
            
            const result = await response.json();
            
            // Show success message
            Swal.fire({
                icon: 'success',
                title: 'Menu Item Added',
                text: result.message,
                showConfirmButton: false,
                timer: 1500
            });
            
            // Reset form
            addMenuItemForm.reset();
            
            // Close modal if it exists
            const modal = bootstrap.Modal.getInstance(document.getElementById('addMenuItemModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reload menu items
            loadMenuItems();
            
        } catch (error) {
            console.error('Error adding menu item:', error);
            showError('Failed to add menu item');
        }
    });
}

// Utility Functions
function getStatusColor(status) {
    switch (status.toLowerCase()) {
        case 'pending':
            return 'warning';
        case 'processing':
            return 'info';
        case 'completed':
            return 'success';
        case 'cancelled':
            return 'danger';
        default:
            return 'secondary';
    }
}

function showError(message) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: message
    });
}

// Debounce function to prevent too many API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
