// Cyber Brew Coffee Shop Frontend Script

document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();
    
    // Check if we are on the cart page
    if (document.getElementById('cart-items-container')) {
        renderCartPage();
    }
});

// --- CART LOGIC ---
function getCart() {
    const cart = localStorage.getItem('cyber_brew_cart');
    return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
    localStorage.setItem('cyber_brew_cart', JSON.stringify(cart));
    updateCartBadge();
}

function addToCart(id, name, price) {
    let cart = getCart();
    const existingIndex = cart.findIndex(item => item.id === id);
    
    if (existingIndex > -1) {
        cart[existingIndex].quantity += 1;
    } else {
        cart.push({
            id: id,
            name: name,
            price: price,
            quantity: 1
        });
    }
    
    saveCart(cart);
    
    // Quick visual notification
    showNotification(`Berhasil menambahkan ${name} ke keranjang!`);
}

function updateQuantity(id, change) {
    let cart = getCart();
    const index = cart.findIndex(item => item.id === id);
    
    if (index > -1) {
        cart[index].quantity += change;
        if (cart[index].quantity <= 0) {
            cart.splice(index, 1);
        }
        saveCart(cart);
        renderCartPage();
    }
}

function removeFromCart(id) {
    let cart = getCart();
    cart = cart.filter(item => item.id !== id);
    saveCart(cart);
    renderCartPage();
}

function clearCart() {
    localStorage.removeItem('cyber_brew_cart');
    updateCartBadge();
}

function updateCartBadge() {
    const badge = document.getElementById('cart-count-badge');
    if (!badge) return;
    
    const cart = getCart();
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    if (totalItems > 0) {
        badge.textContent = totalItems;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

function formatRupiah(number) {
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0
    }).format(number);
}

// --- RENDER CART PAGE ---
function renderCartPage() {
    const container = document.getElementById('cart-items-container');
    const summaryContainer = document.getElementById('cart-summary-container');
    if (!container) return;
    
    const cart = getCart();
    
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="cart-empty">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                </svg>
                <h3>Keranjang Anda Kosong</h3>
                <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Silakan pilih kopi favorit Anda dari katalog menu kami.</p>
                <a href="/menu" class="btn btn-primary">Lihat Menu Kopi</a>
            </div>
        `;
        if (summaryContainer) summaryContainer.style.display = 'none';
        return;
    }
    
    if (summaryContainer) summaryContainer.style.display = 'block';
    
    let html = `
        <table class="cart-table">
            <thead>
                <tr>
                    <th>Produk</th>
                    <th>Harga</th>
                    <th>Jumlah</th>
                    <th>Subtotal</th>
                    <th>Aksi</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let total = 0;
    
    cart.forEach(item => {
        const subtotal = item.price * item.quantity;
        total += subtotal;
        
        html += `
            <tr>
                <td class="cart-item-name">${item.name}</td>
                <td>${formatRupiah(item.price)}</td>
                <td>
                    <div class="quantity-control">
                        <button class="quantity-btn" onclick="updateQuantity(${item.id}, -1)">-</button>
                        <span>${item.quantity}</span>
                        <button class="quantity-btn" onclick="updateQuantity(${item.id}, 1)">+</button>
                    </div>
                </td>
                <td style="font-weight: 600;">${formatRupiah(subtotal)}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="removeFromCart(${item.id})">Hapus</button>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
    
    // Render Summary
    const tax = total * 0.1; // 10% tax
    const finalTotal = total + tax;
    
    if (summaryContainer) {
        summaryContainer.innerHTML = `
            <div class="summary-card">
                <h3 style="margin-bottom: 1.5rem;">Ringkasan Pesanan</h3>
                <div class="summary-row">
                    <span>Subtotal</span>
                    <span>${formatRupiah(total)}</span>
                </div>
                <div class="summary-row">
                    <span>Pajak (10%)</span>
                    <span>${formatRupiah(tax)}</span>
                </div>
                <div class="summary-row total">
                    <span>Total</span>
                    <span>${formatRupiah(finalTotal)}</span>
                </div>
                <button class="btn btn-primary" style="width: 100%;" onclick="processCheckout(${finalTotal})">Checkout Pemesanan</button>
            </div>
        `;
    }
}

// --- CHECKOUT PROCESS ---
function processCheckout(total) {
    const cart = getCart();
    
    fetch('/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            items: cart,
            total: total
        })
    })
    .then(response => {
        if (response.status === 401) {
            showNotification('Silakan login terlebih dahulu untuk melakukan checkout.', 'danger');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
            throw new Error('Unauthorized');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            clearCart();
            showNotification(data.message, 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            showNotification(data.message || 'Gagal memproses pesanan.', 'danger');
        }
    })
    .catch(error => {
        console.error('Checkout error:', error);
    });
}

// --- NOTIFICATION FUNCTION ---
function showNotification(message, type = 'success') {
    // Check if notification container exists, if not create it
    let container = document.getElementById('notification-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '10px';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.margin = '0';
    toast.style.boxShadow = '0 5px 15px rgba(0,0,0,0.3)';
    toast.style.minWidth = '300px';
    toast.style.animation = 'fadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    toast.innerHTML = `
        <span>${message}</span>
        <button style="background:none; border:none; color:inherit; cursor:pointer; font-weight:bold; margin-left:15px;" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.4s ease';
        setTimeout(() => {
            toast.remove();
        }, 400);
    }, 4000);
}
