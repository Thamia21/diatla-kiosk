// Global variables
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let menuData = {};
let stripe = window.stripeKey ? Stripe(window.stripeKey) : null;
let elements;

// Load menu items for a specific category
async function loadMenuItems(category = 'all') {
    try {
        console.log('Loading menu items for category:', category);
        const response = await fetch('/api/menu');
        if (!response.ok) {
            throw new Error('Failed to load menu items');
        }
        
        const menuData = await response.json();
        console.log('Menu data received:', menuData);
        
        const menuContainer = document.getElementById('menu-container');
        if (!menuContainer) {
            console.error('Menu container not found');
            return;
        }
        
        menuContainer.innerHTML = ''; // Clear existing items
        
        if (menuData.length === 0) {
            console.log('No menu items found');
            menuContainer.innerHTML = '<p class="text-center">No menu items available.</p>';
            return;
        }
        
        // If category is 'all', display all categories
        const categoriesToShow = category === 'all' 
            ? menuData 
            : menuData.filter(cat => cat.category.toLowerCase() === category.toLowerCase());
        
        if (categoriesToShow.length === 0) {
            console.log('Category not found:', category);
            menuContainer.innerHTML = '<p class="text-center">No items found in this category.</p>';
            return;
        }
        
        // Display each category's items
        categoriesToShow.forEach(categoryData => {
            console.log(`Processing category: ${categoryData.category}`);
            
            const categorySection = document.createElement('div');
            categorySection.className = 'category-section mb-5';
            categorySection.innerHTML = `
                <h2 class="category-title mb-4">${categoryData.display_name || categoryData.category}</h2>
                <div class="row g-4 menu-items-container">
                    ${categoryData.items.map(item => {
                        // Check if this is specifically a soda or water item
                        const isSoda = item.name.toLowerCase().includes('soda');
                        const isWater = item.name.toLowerCase().includes('water');
                        const needsOptions = isSoda || isWater;
                        
                        // Get drink options if this is a soda or water item
                        const drinkOptions = needsOptions ? getDrinkOptions(item.name) : null;
                        
                        return `
                        <div class="col-md-6 col-lg-4">
                            <div class="menu-item card h-100">
                                ${item.image_url ? `
                                    <img src="${item.image_url}" class="card-img-top menu-item-image" alt="${item.name}">
                                ` : ''}
                                <div class="card-body">
                                    <h5 class="card-title">${item.name}</h5>
                                    <p class="card-text description">${item.description || ''}</p>
                                    <p class="card-text price">R${item.price.toFixed(2)}</p>
                                    ${needsOptions ? `
                                        <div class="form-group mb-3">
                                            <label for="drink-${item.id}" class="form-label">Select ${isSoda ? 'Soda' : 'Water'} Type:</label>
                                            <select class="form-select drink-select" id="drink-${item.id}">
                                                ${drinkOptions.map(option => `
                                                    <option value="${option}">${option}</option>
                                                `).join('')}
                                            </select>
                                        </div>
                                    ` : ''}
                                    <div class="d-flex justify-content-between align-items-center">
                                        <button class="btn btn-primary add-to-cart" onclick="addToCart(${JSON.stringify(item).replace(/"/g, '&quot;')}, ${needsOptions})">
                                            Add to Cart
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `}).join('')}
                </div>
            `;
            menuContainer.appendChild(categorySection);
        });
        
    } catch (error) {
        console.error('Error loading menu items:', error);
        const menuContainer = document.getElementById('menu-container');
        if (menuContainer) {
            menuContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    Failed to load menu items. Please try refreshing the page.
                </div>
            `;
        }
    }
}

// Get drink options based on drink type
function getDrinkOptions(drinkName) {
    drinkName = drinkName.toLowerCase();
    
    if (drinkName.includes('water')) {
        return [
            'Still Water',
            'Sparkling Water'
        ];
    } else if (drinkName.includes('soda')) {
        return [
            'Coca-Cola',
            'Coca-Cola Zero',
            'Fanta Orange',
            'Fanta Grape',
            'Sprite',
            'Sprite Zero',
            'Schweppes Ginger Ale',
            'Schweppes Tonic Water',
            'Stoney Ginger Beer'
        ];
    }
    
    return [];
}

// Add item to cart
function addToCart(item, needsOptions = false) {
    console.log('Adding to cart:', item);
    
    let selectedOption = '';
    if (needsOptions) {
        const drinkSelect = document.getElementById(`drink-${item.id}`);
        if (drinkSelect) {
            selectedOption = drinkSelect.value;
        }
    }
    
    // Check if item with same drink option exists in cart
    const existingItem = cart.find(cartItem => 
        cartItem.id === item.id && 
        cartItem.selectedOption === selectedOption
    );
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: 1,
            selectedOption: selectedOption
        });
    }
    
    // Save updated cart
    localStorage.setItem('cart', JSON.stringify(cart));
    
    // Update cart display
    updateCartDisplay();
    
    // Show success message with drink option if selected
    const itemName = selectedOption 
        ? `${item.name} (${selectedOption})` 
        : item.name;
        
    Swal.fire({
        title: 'Added to Cart! 🛒',
        html: `<div class="swal-add-cart">
            <div class="item-name">${itemName}</div>
            <div class="item-price">R${item.price.toFixed(2)}</div>
        </div>`,
        icon: 'success',
        showConfirmButton: false,
        timer: 1500,
        timerProgressBar: true,
        position: 'top-end',
        toast: true,
        background: '#4CAF50',
        color: '#fff',
        iconColor: '#fff',
        customClass: {
            popup: 'animated bounceIn'
        }
    });
}

// Update item quantity
function updateQuantity(itemId, change, selectedOption = '') {
    const item = cart.find(item => 
        item.id === itemId && 
        item.selectedOption === selectedOption
    );
    
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            cart = cart.filter(i => 
                !(i.id === itemId && i.selectedOption === selectedOption)
            );
        }
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartDisplay();
    }
}

// Update cart display
function updateCartDisplay() {
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');
    const cartCount = document.querySelector('.cart-count');
    
    if (!cartItems || !cartTotal || !cartCount) {
        console.error('Cart elements not found');
        return;
    }
    
    // Clear existing items
    cartItems.innerHTML = '';
    
    // Calculate total and update display
    let total = 0;
    let itemCount = 0;
    
    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        itemCount += item.quantity;
        
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-item';
        itemElement.innerHTML = `
            <div class="cart-item-details">
                <h4>${item.name}${item.selectedOption ? ` (${item.selectedOption})` : ''}</h4>
                <p>R${item.price.toFixed(2)} each</p>
            </div>
            <div class="cart-item-controls">
                <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, -1, '${item.selectedOption}')">-</button>
                <span class="quantity">${item.quantity}</span>
                <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, 1, '${item.selectedOption}')">+</button>
            </div>
            <div class="cart-item-total">
                R${itemTotal.toFixed(2)}
            </div>
        `;
        cartItems.appendChild(itemElement);
    });
    
    // Update total and item count
    cartTotal.textContent = total.toFixed(2);
    cartCount.textContent = itemCount;
    
    // Show/hide empty cart message
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="text-center">Your cart is empty</p>';
    }
}

// Handle payment method selection
async function handlePaymentMethodSelection(paymentMethod, orderData) {
    try {
        // Show loading state
        Swal.fire({
            title: 'Processing Order...',
            html: '<div class="loading-animation"></div>',
            allowOutsideClick: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        console.log('Processing order with payment method:', paymentMethod);
        console.log('Order data:', orderData);

        // Create order first
        const orderResponse = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                customerName: orderData.customerName,
                customerEmail: orderData.customerEmail,
                customerPhone: orderData.customerPhone,
                specialInstructions: orderData.specialInstructions,
                items: orderData.items,
                totalAmount: orderData.totalAmount,
                paymentMethod: paymentMethod
            })
        });

        if (!orderResponse.ok) {
            throw new Error('Failed to create order');
        }

        const orderResult = await orderResponse.json();
        console.log('Order created:', orderResult);

        if (paymentMethod === 'card') {
            // For card payments, redirect to payment page
            window.location.href = `/payment?order_id=${orderResult.order.id}&amount=${orderData.totalAmount}`;
        } else {
            // Handle cash or EFT payment
            Swal.fire({
                icon: 'success',
                title: 'Order Placed Successfully! 🎉',
                html: `
                    <div class="order-success">
                        <h3>Order #${orderResult.order.order_number}</h3>
                        <p>Thank you for your order!</p>
                        <div class="payment-instructions">
                            <h4>Payment Instructions (${paymentMethod.toUpperCase()})</h4>
                            ${paymentMethod === 'cash' ? 
                                '<p>Please proceed to the counter to make your payment.</p>' :
                                '<p>Please use your order number as reference when making the EFT payment.</p>'
                            }
                        </div>
                    </div>
                `,
                confirmButtonText: 'Done',
                allowOutsideClick: false,
                customClass: {
                    popup: 'animated bounceInDown',
                    title: 'order-success-title',
                    content: 'order-success-content',
                    confirmButton: 'order-success-button'
                }
            }).then(() => {
                // Clear cart and close modal
                cart = [];
                localStorage.setItem('cart', JSON.stringify(cart));
                orderSummaryModal.style.display = 'none';
                updateCartDisplay();
            });
        }
    } catch (error) {
        console.error('Error processing order:', error);
        Swal.fire({
            icon: 'error',
            title: 'Oops! 😕',
            text: 'There was an error processing your order. Please try again.',
            confirmButtonText: 'Try Again',
            customClass: {
                popup: 'animated shake'
            }
        });
    }
}

// Show welcome message
async function showWelcomeMessage() {
    try {
        // Step 1: Welcome
        const result1 = await Swal.fire({
            title: 'Welcome to Diatla! 👋',
            html: `
                <div class="welcome-step">
                    <div class="welcome-text animated fadeIn">
                        <h3>Your Premier Dining Destination</h3>
                        <p>Experience the finest in South African cuisine</p>
                    </div>
                    <div class="features-grid animated fadeInUp">
                        <div class="feature-item">
                            <i class='bx bx-restaurant'></i>
                            <span>Fine Dining</span>
                        </div>
                        <div class="feature-item">
                            <i class='bx bx-time-five'></i>
                            <span>Quick Service</span>
                        </div>
                        <div class="feature-item">
                            <i class='bx bx-heart'></i>
                            <span>Made with Love</span>
                        </div>
                    </div>
                </div>
            `,
            confirmButtonText: 'Next →',
            allowOutsideClick: false,
            allowEscapeKey: false,
            customClass: {
                confirmButton: 'btn btn-primary welcome-button'
            }
        });

        if (!result1.isConfirmed) {
            return;
        }

        // Step 2: Today's Specials
        const result2 = await Swal.fire({
            title: 'Today\'s Specials! 🌟',
            html: `
                <div class="specials-step">
                    <div class="special-item animated fadeInLeft">
                        <i class='bx bx-food-menu'></i>
                        <h4>Chef's Special</h4>
                        <p>Grilled T-Bone Steak</p>
                        <span class="discount">20% OFF</span>
                    </div>
                    <div class="special-item animated fadeInRight">
                        <i class='bx bx-drink'></i>
                        <h4>Drink of the Day</h4>
                        <p>Fresh Fruit Smoothie</p>
                        <span class="discount">Buy 1 Get 1 Free</span>
                    </div>
                    <div class="promotion-banner animated fadeInUp">
                        <p>🎉 Happy Hour: 4PM - 6PM</p>
                        <p>All beverages at special prices!</p>
                    </div>
                </div>
            `,
            confirmButtonText: 'Next →',
            allowOutsideClick: false,
            allowEscapeKey: false,
            customClass: {
                confirmButton: 'btn btn-primary welcome-button'
            }
        });

        if (!result2.isConfirmed) {
            return;
        }

        // Step 3: Start Ordering
        const result3 = await Swal.fire({
            title: 'Ready to Order? 🍽️',
            html: `
                <div class="order-step">
                    <div class="order-instructions animated fadeIn">
                        <h3>How to Order:</h3>
                        <ol>
                            <li>Browse our delicious menu</li>
                            <li>Add items to your cart</li>
                            <li>Review your order</li>
                            <li>Choose payment method</li>
                            <li>Enjoy your meal!</li>
                        </ol>
                    </div>
                    <div class="start-message animated bounceIn">
                        <p>Your culinary journey begins now!</p>
                    </div>
                </div>
            `,
            confirmButtonText: 'Start Ordering!',
            allowOutsideClick: false,
            allowEscapeKey: false,
            customClass: {
                confirmButton: 'btn btn-success welcome-button'
            }
        });

        if (result3.isConfirmed) {
            // Store welcome status
            localStorage.setItem('welcomed', 'true');
            
            // Close any remaining modals
            Swal.close();
            
            // Load menu items after a short delay to ensure modal is closed
            setTimeout(() => {
                loadMenuItems('all');
            }, 100);
        }
    } catch (error) {
        console.error('Error showing welcome message:', error);
        Swal.close();
    }
}

// Admin order management functions
async function viewOrderDetails(orderId) {
    try {
        const response = await fetch(`/api/order/${orderId}`);
        const data = await response.json();
        
        if (data.success) {
            const order = data.order;
            let itemsHtml = order.items.map(item => `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.quantity}</td>
                    <td>R${item.price.toFixed(2)}</td>
                    <td>R${item.total.toFixed(2)}</td>
                </tr>
            `).join('');
            
            Swal.fire({
                title: `Order Details - ${order.order_number}`,
                html: `
                    <div class="order-details">
                        <p><strong>Customer Name:</strong> ${order.customer_name}</p>
                        <p><strong>Email:</strong> ${order.customer_email}</p>
                        <p><strong>Phone:</strong> ${order.customer_phone}</p>
                        <p><strong>Order Date:</strong> ${order.created_at}</p>
                        <p><strong>Status:</strong> ${order.status}</p>
                        <p><strong>Payment Method:</strong> ${order.payment_method}</p>
                        <p><strong>Special Instructions:</strong> ${order.special_instructions || 'None'}</p>
                        
                        <h4>Order Items:</h4>
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
                                ${itemsHtml}
                            </tbody>
                        </table>
                        
                        <p class="total"><strong>Total Amount:</strong> R${order.total_amount.toFixed(2)}</p>
                    </div>
                `,
                width: '600px',
                confirmButtonText: 'Close'
            });
        } else {
            throw new Error(data.message || 'Failed to get order details');
        }
    } catch (error) {
        console.error('Error viewing order:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to load order details'
        });
    }
}

async function processOrder(orderId) {
    try {
        const result = await Swal.fire({
            title: 'Process Order',
            text: 'Are you sure you want to start processing this order?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Yes, process it',
            cancelButtonText: 'No, cancel'
        });
        
        if (result.isConfirmed) {
            const response = await fetch(`/api/order/${orderId}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: 'Order status updated to processing'
                }).then(() => {
                    // Reload the page to refresh the order list
                    window.location.reload();
                });
            } else {
                throw new Error(data.message || 'Failed to process order');
            }
        }
    } catch (error) {
        console.error('Error processing order:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Failed to process order'
        });
    }
}

async function cancelOrder(orderId) {
    try {
        const result = await Swal.fire({
            title: 'Cancel Order',
            text: 'Are you sure you want to cancel this order?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, cancel it',
            cancelButtonText: 'No, keep it',
            confirmButtonColor: '#d33'
        });
        
        if (result.isConfirmed) {
            const response = await fetch(`/api/order/${orderId}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: 'Order cancelled successfully'
                }).then(() => {
                    // Reload the page to refresh the order list
                    window.location.reload();
                });
            } else {
                throw new Error(data.message || 'Failed to cancel order');
            }
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Failed to cancel order'
        });
    }
}

// Add event listeners to the buttons
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking welcome status...');
    console.log('Welcome status:', localStorage.getItem('welcomed'));
    
    // Show welcome message if not shown before
    if (!localStorage.getItem('welcomed')) {
        showWelcomeMessage();
    } else {
        // Load menu items directly if already welcomed
        loadMenuItems('all');
    }
    
    // Reset welcome message after 24 hours
    const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
    setInterval(() => {
        localStorage.removeItem('welcomed');
    }, TWENTY_FOUR_HOURS);
    
    // Load initial menu items (all categories)
    // loadMenuItems('all');
    
    // Add click event listeners to category navigation
    document.querySelectorAll('.nav-item').forEach(navItem => {
        navItem.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Add active class to clicked nav item
            this.classList.add('active');
            
            // Get category from data attribute
            const category = this.getAttribute('data-category');
            loadMenuItems(category);
        });
    });
    
    // View order buttons
    document.querySelectorAll('.view-order-btn').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            viewOrderDetails(orderId);
        });
    });
    
    // Process order buttons
    document.querySelectorAll('.process-order-btn').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            processOrder(orderId);
        });
    });
    
    // Cancel order buttons
    document.querySelectorAll('.cancel-order-btn').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            cancelOrder(orderId);
        });
    });
    
    // Get cart elements
    const cartIcon = document.getElementById('cartIcon');
    const cartModal = document.getElementById('cartModal');
    const closeCartBtn = document.getElementById('closeCart');
    const orderSummaryModal = document.getElementById('orderSummaryModal');
    const closeOrderSummaryBtn = document.getElementById('closeOrderSummary');
    const confirmOrderBtn = document.getElementById('confirmOrder');
    const editOrderBtn = document.getElementById('editOrder');
    const customerForm = document.getElementById('customerForm');
    
    // Handle cart icon click
    if (cartIcon) {
        cartIcon.onclick = function() {
            cartModal.style.display = 'block';
            updateCartDisplay();
        }
    }
    
    // Handle close cart
    if (closeCartBtn) {
        closeCartBtn.onclick = function() {
            cartModal.style.display = 'none';
        }
    }
    
    // Handle close order summary
    if (closeOrderSummaryBtn) {
        closeOrderSummaryBtn.onclick = function() {
            orderSummaryModal.style.display = 'none';
        }
    }
    
    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target == cartModal) {
            cartModal.style.display = 'none';
        }
        if (event.target == orderSummaryModal) {
            orderSummaryModal.style.display = 'none';
        }
    }
    
    // Handle confirm order
    if (confirmOrderBtn) {
        confirmOrderBtn.onclick = async function() {
            // Get form data
            const formData = new FormData(customerForm);
            const orderData = {
                customerName: formData.get('name'),
                customerEmail: formData.get('email'),
                customerPhone: formData.get('phone'),
                specialInstructions: formData.get('specialInstructions'),
                items: cart.map(item => ({
                    id: item.id,
                    name: item.name,
                    quantity: item.quantity,
                    price: item.price,
                    selectedOption: item.selectedOption
                })),
                totalAmount: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0)
            };
            
            // Get selected payment method
            const paymentMethod = document.getElementById('paymentMethod').value;
            if (!paymentMethod) {
                Swal.fire({
                    icon: 'error',
                    title: 'Payment Method Required',
                    text: 'Please select a payment method to continue.'
                });
                return;
            }
            
            // Process the order based on payment method
            handlePaymentMethodSelection(paymentMethod, orderData);
        }
    }
    
    // Handle edit order
    if (editOrderBtn) {
        editOrderBtn.onclick = function() {
            orderSummaryModal.style.display = 'none';
            cartModal.style.display = 'block';
        }
    }
    
    // Handle form submission for order review
    if (customerForm) {
        const requiredFields = customerForm.querySelectorAll('[required]');
        
        customerForm.onsubmit = function(e) {
            e.preventDefault();
            
            // Check if cart is empty
            if (cart.length === 0) {
                Swal.fire({
                    icon: 'error',
                    title: 'Empty Cart',
                    text: 'Please add items to your cart before proceeding.'
                });
                return;
            }
            
            // Validate required fields
            let isValid = true;
            requiredFields.forEach(field => {
                if (!field.value) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                Swal.fire({
                    icon: 'error',
                    title: 'Missing Information',
                    text: 'Please fill in all required fields.'
                });
                return;
            }
            
            // Hide cart modal and show order summary
            cartModal.style.display = 'none';
            orderSummaryModal.style.display = 'block';
            
            // Get customer details
            const customerName = document.getElementById('name').value;
            const customerEmail = document.getElementById('email').value;
            const customerPhone = document.getElementById('phone').value;
            const specialInstructions = document.getElementById('specialInstructions').value;
            const paymentMethod = document.getElementById('paymentMethod').value;

            // Update customer details in summary
            const customerDetails = document.getElementById('orderSummaryCustomer');
            if (customerDetails) {
                customerDetails.innerHTML = `
                    <div class="customer-info">
                        <p><strong>Name:</strong> ${customerName}</p>
                        <p><strong>Email:</strong> ${customerEmail}</p>
                        <p><strong>Phone:</strong> ${customerPhone}</p>
                        ${specialInstructions ? `<p><strong>Special Instructions:</strong> ${specialInstructions}</p>` : ''}
                        <p><strong>Payment Method:</strong> ${paymentMethod.charAt(0).toUpperCase() + paymentMethod.slice(1)}</p>
                    </div>
                `;
            }
            
            // Update order items in summary
            const orderItems = document.getElementById('orderSummaryItems');
            const orderTotal = document.getElementById('orderSummaryTotal');
            
            if (orderItems && orderTotal) {
                orderItems.innerHTML = cart.map(item => `
                    <div class="order-summary-item">
                        <span class="item-name">${item.name}${item.selectedOption ? ` (${item.selectedOption})` : ''}</span>
                        <span class="item-quantity">x${item.quantity}</span>
                        <span class="item-total">R${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                `).join('');
                
                const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
                orderTotal.textContent = total.toFixed(2);
            }
        }
    }
});
