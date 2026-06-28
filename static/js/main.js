// Cyber Brew Coffee Shop Frontend Script

document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();
    
    // Check if we are on the cart page
    if (document.getElementById('cart-items-container')) {
        renderCartPage();
    }
    
    // Initialize World Cup predictions if we are on the index page
    if (document.getElementById('predict-widget-argentina-france') || document.getElementById('predict-widget-brazil-england')) {
        initPredictions();
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
    const activeCoupon = localStorage.getItem('cyber_brew_coupon');
    const hasDiscount = activeCoupon === 'PIALADUNIA2026';
    const discount = hasDiscount ? total * 0.15 : 0;
    const subtotalAfterDiscount = total - discount;
    const tax = subtotalAfterDiscount * 0.1; // 10% tax
    const finalTotal = subtotalAfterDiscount + tax;
    
    if (summaryContainer) {
        let summaryHtml = `
            <div class="summary-card">
                <h3 style="margin-bottom: 1.5rem;">Ringkasan Pesanan</h3>
                <div class="summary-row">
                    <span>Subtotal</span>
                    <span>${formatRupiah(total)}</span>
                </div>
        `;
        
        if (hasDiscount) {
            summaryHtml += `
                <div class="summary-row" style="color: var(--secure-green); font-weight: 600;">
                    <span>Diskon (15% Piala Dunia)</span>
                    <span>-${formatRupiah(discount)}</span>
                </div>
            `;
        }
        
        summaryHtml += `
                <div class="summary-row">
                    <span>Pajak (10%)</span>
                    <span>${formatRupiah(tax)}</span>
                </div>
                <div class="summary-row total">
                    <span>Total</span>
                    <span>${formatRupiah(finalTotal)}</span>
                </div>
                
                <div class="coupon-section">
                    <label style="font-size: 0.85rem; color: var(--text-muted); display: block; margin-bottom: 0.5rem;">Kode Promo Piala Dunia</label>
                    <div class="coupon-form">
                        <input type="text" id="coupon-input" class="form-control" placeholder="Contoh: PIALADUNIA2026" style="padding: 0.4rem 0.6rem; font-size: 0.85rem; border-radius: 4px;" ${hasDiscount ? 'value="PIALADUNIA2026" disabled' : ''}>
                        <button class="btn btn-secondary btn-sm" onclick="${hasDiscount ? 'removeCoupon()' : 'applyCoupon()'}">${hasDiscount ? 'Hapus' : 'Pakai'}</button>
                    </div>
                    <div id="coupon-message" class="coupon-msg"></div>
                </div>
                
                <button class="btn btn-primary" style="width: 100%; margin-top: 1.5rem;" onclick="processCheckout(${finalTotal})">Checkout Pemesanan</button>
            </div>
        `;
        summaryContainer.innerHTML = summaryHtml;
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

// --- AUTO LOGOUT / INACTIVITY TIMER (30 seconds) ---
let inactivityTimer;
const INACTIVITY_LIMIT = 30000; // 30 seconds

function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
        // Only logout if the logout button is present (user is logged in)
        if (document.querySelector('a[href="/logout"]')) {
            showNotification("Sesi Anda telah berakhir (30 detik tidak aktif). Mengalihkan...", "warning");
            setTimeout(() => {
                window.location.href = '/logout';
            }, 1500);
        }
    }, INACTIVITY_LIMIT);
}

// Start timer if logged in
if (document.querySelector('a[href="/logout"]')) {
    resetInactivityTimer();
    // Listen for user activity to reset the timer
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    activityEvents.forEach(event => {
        document.addEventListener(event, resetInactivityTimer, true);
    });
}

// --- COUPON ACTIONS ---
function applyCoupon() {
    const input = document.getElementById('coupon-input');
    const msg = document.getElementById('coupon-message');
    if (!input || !msg) return;
    
    const code = input.value.trim().toUpperCase();
    if (code === 'PIALADUNIA2026') {
        localStorage.setItem('cyber_brew_coupon', 'PIALADUNIA2026');
        msg.className = 'coupon-msg success';
        msg.textContent = 'Kupon berhasil diterapkan! Anda mendapatkan potongan 15%.';
        setTimeout(() => {
            renderCartPage();
        }, 1000);
    } else if (code === '') {
        msg.className = 'coupon-msg error';
        msg.textContent = 'Silakan masukkan kode kupon terlebih dahulu.';
    } else {
        msg.className = 'coupon-msg error';
        msg.textContent = 'Kode kupon salah atau tidak berlaku.';
    }
}

function removeCoupon() {
    localStorage.removeItem('cyber_brew_coupon');
    renderCartPage();
}

// --- WORLD CUP PREDICTIONS WIDGET ---
function initPredictions() {
    const predictions = JSON.parse(localStorage.getItem('cyber_brew_predictions') || '{}');
    Object.keys(predictions).forEach(matchKey => {
        const parts = matchKey.split('_vs_');
        if (parts.length === 2) {
            const team1 = parts[0];
            const team2 = parts[1];
            renderPredictionState(team1, team2, predictions[matchKey]);
        }
    });
}

function makePrediction(team1, team2, prediction) {
    // Check if user is logged in by looking for logout button or active username
    const logoutBtn = document.querySelector('a[href="/logout"]');
    if (!logoutBtn) {
        showNotification("Silakan login terlebih dahulu untuk membuat prediksi!", "warning");
        return;
    }
    
    const predictions = JSON.parse(localStorage.getItem('cyber_brew_predictions') || '{}');
    const matchKey = `${team1}_vs_${team2}`;
    predictions[matchKey] = prediction;
    localStorage.setItem('cyber_brew_predictions', JSON.stringify(predictions));
    
    renderPredictionState(team1, team2, prediction);
    
    // Auto-grant the coupon in local storage to make it easy for them
    localStorage.setItem('cyber_brew_coupon', 'PIALADUNIA2026');
    
    showNotification(`⚽ Prediksi berhasil! Anda menjagokan ${prediction}. Kode kupon PIALADUNIA2026 telah ditambahkan ke keranjang belanja Anda!`, 'success');
}

function renderPredictionState(team1, team2, prediction) {
    const widgetId = `predict-widget-${team1.toLowerCase()}-${team2.toLowerCase()}`;
    const widget = document.getElementById(widgetId);
    if (!widget) return;
    
    widget.innerHTML = `
        <div style="text-align: center; background-color: rgba(16, 185, 129, 0.1); border: 1px solid var(--primary); padding: 0.8rem; border-radius: 6px; animation: fadeIn 0.4s ease-out;">
            <p style="font-size: 0.85rem; font-weight: 600; color: var(--primary); margin-bottom: 0.3rem;">⚽ Prediksi Anda Disimpan!</p>
            <p style="font-size: 0.8rem; color: var(--text-light);">Pilihan: <strong>${prediction}</strong></p>
            <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Kupon <strong>PIALADUNIA2026</strong> otomatis aktif di keranjang!</p>
        </div>
    `;
}
