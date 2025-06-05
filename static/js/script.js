// Smooth scroll for navigation links
document.addEventListener('DOMContentLoaded', function() {
    const tables = [
        { id: 'inventory-table', selector: '#inventory-table' },
        { id: 'dashboard-inventory-table', selector: '#dashboard-inventory-table' }
    ];

    tables.forEach(tableConfig => {
        if (document.getElementById(tableConfig.id)) {
            const table = $(tableConfig.selector).DataTable({
                processing: true,
                serverSide: true,
                responsive: true,
                ajax: {
                    url: '/get_datatables_inventory',
                    type: 'GET',
                    data: function(d) {
                        d.user_id = '{{ session.get("user_id") }}';
                    },
                    error: function(xhr, error, thrown) {
                        console.error('DataTables AJAX Error:', {
                            status: xhr.status,
                            statusText: xhr.statusText,
                            responseText: xhr.responseText,
                            error: error,
                            thrown: thrown
                        });
                        showNotification('Failed to load inventory data. Status: ' + xhr.status, 'error');
                    }
                },
                columns: tableConfig.id === 'dashboard-inventory-table' ? [
                    { data: 'name' },
                    { data: 'category' },
                    { data: 'stock' },
                    {
                        data: 'price',
                        render: function(data) {
                            return '$' + parseFloat(data).toFixed(2);
                        }
                    }
                ] : [
                    { data: 'sku' },
                    { data: 'name' },
                    { data: 'category' },
                    { data: 'stock' },
                    {
                        data: 'price',
                        render: function(data) {
                            return '$' + parseFloat(data).toFixed(2);
                        }
                    },
                    { data: 'status' },
                    {
                        data: null,
                        render: function(data, type, row) {
                            return `
                                <button class="action-btn edit-btn" onclick="editRow('${row.id}', '${tableConfig.id}')">Edit</button>
                                <button class="action-btn delete-btn" onclick="deleteRow('${row.id}', '${tableConfig.id}')">Delete</button>
                            `;
                        },
                        orderable: false
                    }
                ],
                createdRow: function(row, data, dataIndex) {
                    if (tableConfig.id === 'inventory-table') {
                        $(row).attr('data-id', data.id);
                    }
                },
                pageLength: 5,
                lengthMenu: [5, 10, 25, 50],
                searching: true,
                ordering: true,
                language: {
                    emptyTable: "No inventory items available.",
                    processing: "Loading..."
                }
            });

            window[tableConfig.id] = table;
        }
    });

    window.editRow = function(itemId, tableId) {
        const table = window[tableId];
        const rowData = table.data().toArray().find(row => row.id == itemId);
        if (!rowData) {
            showNotification('Item not found.', 'error');
            return;
        }

        let rowNode = null;
        table.rows().every(function() {
            if (this.data().id == itemId) {
                rowNode = this.node();
                return false;
            }
            return true;
        });

        if (!rowNode) {
            showNotification('Item is not on the current page.', 'error');
            return;
        }

        $(rowNode).addClass('edit-mode').attr('data-id', itemId);
        $(rowNode).html(`
            <td>${rowData.sku}</td>
            <td><input type="text" id="edit-name-${itemId}" value="${rowData.name}"></td>
            <td>
                <select id="edit-category-${itemId}">
                    <option value="Grocery" ${rowData.category === 'Grocery' ? 'selected' : ''}>Grocery</option>
                    <option value="Tech" ${rowData.category === 'Tech' ? 'selected' : ''}>Tech</option>
                    <option value="Daily Essentials" ${rowData.category === 'Daily Essentials' ? 'selected' : ''}>Daily Essentials</option>
                    <option value="Clothing" ${rowData.category === 'Clothing' ? 'selected' : ''}>Clothing</option>
                    <option value="Home Appliances" ${rowData.category === 'Home Appliances' ? 'selected' : ''}>Home Appliances</option>
                </select>
            </td>
            <td><input type="number" id="edit-stock-${itemId}" value="${rowData.stock}" min="0"></td>
            <td><input type="number" id="edit-price-${itemId}" value="${rowData.price}" step="0.01" min="0"></td>
            <td>
                <select id="edit-status-${itemId}">
                    <option value="Pending" ${rowData.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="In Progress" ${rowData.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="Completed" ${rowData.status === 'Completed' ? 'selected' : ''}>Completed</option>
                </select>
            </td>
            <td>
                <button class="action-btn save-btn" onclick="saveRow('${itemId}', '${tableId}')">Save</button>
                <button class="action-btn cancel-btn" onclick="cancelEdit('${itemId}', '${tableId}')">Cancel</button>
            </td>
        `);
    };

    window.saveRow = function(itemId, tableId) {
        const table = window[tableId];
        const name = $(`#edit-name-${itemId}`).val();
        const category = $(`#edit-category-${itemId}`).val();
        const stock = $(`#edit-stock-${itemId}`).val();
        const price = $(`#edit-price-${itemId}`).val();
        const status = $(`#edit-status-${itemId}`).val();

        if (!name || !category || stock === '' || price === '') {
            showNotification('All fields are required.', 'error');
            return;
        }
        if (isNaN(stock) || stock < 0 || isNaN(price) || price < 0) {
            showNotification('Stock and price must be non-negative numbers.', 'error');
            return;
        }

        $.ajax({
            url: '/update-inventory-item',
            type: 'POST',
            data: {
                item_id: itemId,
                name: name,
                category: category,
                stock: stock,
                price: price,
                status: status,
                _ajax: true
            },
            success: function(response) {
                table.ajax.reload(null, false);
                showNotification(response.success || 'Item updated successfully!', 'success');
            },
            error: function(xhr) {
                console.error('Update Error:', xhr.responseText);
                showNotification(xhr.responseJSON?.error || 'Failed to update item.', 'error');
            }
        });
    };

    window.cancelEdit = function(itemId, tableId) {
        const table = window[tableId];
        table.ajax.reload(null, false);
    };

    window.deleteRow = function(itemId, tableId) {
        if (!confirm('Are you sure you want to delete this item?')) {
            return;
        }
        const table = window[tableId];
        $.ajax({
            url: '/delete-inventory-item',
            type: 'POST',
            data: { item_id: itemId, _ajax: true },
            success: function(response) {
                table.ajax.reload(null, false);
                showNotification(response.success || 'Item deleted successfully!', 'success');
            },
            error: function(xhr) {
                showNotification(xhr.responseJSON?.error || 'Failed to delete item.', 'error');
            }
        });
    };

    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `flash ${type}`;
        notification.textContent = message;
        const container = document.querySelector('.flash-messages') || document.body;
        container.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Newsletter subscription functionality
    const newsletterForm = document.getElementById('newsletter-form');
    const emailInput = document.getElementById('email-input');
    
    if (newsletterForm && emailInput) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = emailInput.value.trim();
            
            // Basic email validation
            if (validateEmail(email)) {
                // Add loading state
                newsletterForm.classList.add('loading');
                
                // Simulate API call delay
                setTimeout(() => {
                    alert('Subscribed successfully! Thank you for joining SME Analytics.');
                    emailInput.value = '';
                    newsletterForm.classList.remove('loading');
                }, 1000);
            } else {
                alert('Please enter a valid email address.');
                emailInput.focus();
            }
        });
    }
    
    // Add scroll effect for navigation bar
    const header = document.querySelector('.header');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add shadow when scrolled
        if (scrollTop > 100) {
            header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
        } else {
            header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
        
        lastScrollTop = scrollTop;
    });
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for scroll animations
    const animateElements = document.querySelectorAll('.feature-card, .testimonial-card, .feature-showcase');
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Mobile menu toggle
    const createMobileMenu = () => {
        const navContainer = document.querySelector('.nav-container');
        const navLinks = document.querySelector('.nav-links');
        
        const mobileMenuBtn = document.createElement('button');
        mobileMenuBtn.classList.add('mobile-menu-btn');
        mobileMenuBtn.innerHTML = '☰';
        mobileMenuBtn.style.display = 'none';
        mobileMenuBtn.style.background = 'none';
        mobileMenuBtn.style.border = 'none';
        mobileMenuBtn.style.fontSize = '1.5rem';
        mobileMenuBtn.style.cursor = 'pointer';
        mobileMenuBtn.style.color = '#333';
        
        const navButtons = document.querySelector('.nav-buttons');
        navContainer.insertBefore(mobileMenuBtn, navButtons);
        
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
        });
        
        const handleResize = () => {
            if (window.innerWidth <= 768) {
                mobileMenuBtn.style.display = 'block';
                navLinks.style.display = 'none';
                navLinks.style.flexDirection = 'column';
                navLinks.style.position = 'absolute';
                navLinks.style.top = '100%';
                navLinks.style.left = '0';
                navLinks.style.right = '0';
                navLinks.style.background = '#f8f9fa';
                navLinks.style.padding = '1rem';
                navLinks.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            } else {
                mobileMenuBtn.style.display = 'none';
                navLinks.style.display = 'flex';
                navLinks.style.flexDirection = 'row';
                navLinks.style.position = 'static';
                navLinks.style.background = 'transparent';
                navLinks.style.padding = '0';
                navLinks.style.boxShadow = 'none';
            }
        };
        
        window.addEventListener('resize', handleResize);
        handleResize();
    };
    
    createMobileMenu();
    
    // Add loading animations to charts
    const animateCharts = () => {
        const chartBars = document.querySelectorAll('.chart-bar, .bar');
        chartBars.forEach((bar, index) => {
            setTimeout(() => {
                bar.style.animation = 'growUp 1s ease-out forwards';
            }, index * 200);
        });
    };
    
    const heroObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCharts();
                heroObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        heroObserver.observe(heroSection);
    }
    
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.6)';
            ripple.style.transform = 'scale(0)';
            ripple.style.animation = 'ripple 0.6s linear';
            ripple.style.left = (e.clientX - e.target.offsetLeft) + 'px';
            ripple.style.top = (e.clientY - e.target.offsetTop) + 'px';
            ripple.style.width = ripple.style.height = '10px';
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function scrollToElement(elementId, offset = 80) {
    const element = document.getElementById(elementId);
    if (element) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const navLinks = document.querySelector('.nav-links');
        if (window.innerWidth <= 768 && navLinks.style.display === 'flex') {
            navLinks.style.display = 'none';
        }
    }
});


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

const debouncedScroll = debounce(function() {
}, 16);

window.addEventListener('scroll', debouncedScroll);

function manageFocus() {
    const focusableElements = document.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
    );
    
    focusableElements.forEach(element => {
        element.addEventListener('focus', function() {
            this.style.outline = '2px solid #26A69A';
            this.style.outlineOffset = '2px';
        });
        
        element.addEventListener('blur', function() {
            this.style.outline = 'none';
        });
    });
}

manageFocus();

document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.style.display = 'none';
            console.warn('Failed to load image:', this.src);
        });
    });
});

loginForm.addEventListener('submit', (e) => {
    console.log("Login form submitted");
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email || !email.includes('@') || !email.includes('.')) {
        e.preventDefault();
        alert('Please enter a valid email');
        return;
    }

    if (!password || password.length < 6) {
        e.preventDefault();
        alert('Password must be at least 6 characters long');
        return;
    }
});

function toggleAddItemForm() {
            const form = document.getElementById('addItemForm');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }

button.addEventListener('click', function() {
    console.log('Edit mode inputs:', row.querySelectorAll('.edit-mode input, .edit-mode select'));
});

window.saveRow = function(itemId, tableId) {
    const table = window[tableId];
    const name = $(`#edit-name-${itemId}`).val();
    const category = $(`#edit-category-${itemId}`).val();
    const stock = $(`#edit-stock-${itemId}`).val();
    const price = $(`#edit-price-${itemId}`).val();
    const status = $(`#edit-status-${itemId}`).val();

    console.log('Saving:', { itemId, name, category, stock, price, status });

    if (!name || !category || stock === '' || price === '') {
        showNotification('All fields are required.', 'error');
        return;
    }
    if (isNaN(stock) || stock < 0 || isNaN(price) || price < 0) {
        showNotification('Stock and price must be non-negative numbers.', 'error');
        return;
    }

    $.ajax({
        url: '/update-inventory-item',
        type: 'POST',
        data: {
            item_id: itemId,
            name: name,
            category: category,
            stock: stock,
            price: price,
            status: status,
            _ajax: true
        },
        success: function(response) {
            console.log('Success:', response);
            table.ajax.reload(null, false);
            showNotification(response.success || 'Item updated successfully!', 'success');
        },
        error: function(xhr) {
            console.error('Update Error:', xhr.status, xhr.responseText);
            showNotification(xhr.responseJSON?.error || 'Failed to update item.', 'error');
        }
    });
};



console.log('%c🚀 Welcome to SME Analytics!', 'color: #26A69A; font-size: 16px; font-weight: bold;');
console.log('%cEmpowering Nepali SMEs with no-code analytics since 2025', 'color: #666; font-size: 12px;');