const state = {
  amount: 250,
  quantity: 1,
  cart: null,
  checkoutStarted: false,
};

const DELIVERY_LABELS = {
  instant: 'send immediately',
  scheduled: 'schedule for tomorrow morning',
  approval: 'hold for manager approval',
};

function dollars(value) {
  return `$${Number(value).toLocaleString('en-US')}`;
}

function selectedAmount() {
  const amountSelect = document.querySelector('#amountSelect');
  return Number(amountSelect.value);
}

function selectedQuantity() {
  const quantityInput = document.querySelector('#quantityInput');
  const quantity = Math.min(10, Math.max(1, Number(quantityInput.value || 1)));
  quantityInput.value = String(quantity);
  return quantity;
}

function syncDenominationControls(amount) {
  const amountSelect = document.querySelector('#amountSelect');
  amountSelect.value = String(amount);
  for (const input of document.querySelectorAll('input[name="amount"]')) {
    input.checked = input.value === String(amount);
  }
}

function updateProductSubtotal() {
  state.amount = selectedAmount();
  state.quantity = selectedQuantity();
  document.querySelector('#productSubtotal').textContent = dollars(state.amount * state.quantity);
  document.querySelector('#productSubtotalNote').textContent =
    `${state.quantity} digital gift card${state.quantity > 1 ? 's' : ''}`;
}

function cartTotal() {
  return state.cart ? state.cart.amount * state.cart.quantity : 0;
}

function renderCart() {
  const cartCount = document.querySelector('#cartCount');
  const cartSubtotal = document.querySelector('#cartSubtotal');
  const cartLineItems = document.querySelector('#cartLineItems');
  const cartEmptyState = document.querySelector('#cartEmptyState');
  const proceedButton = document.querySelector('#proceedCheckoutButton');

  if (!state.cart) {
    cartCount.textContent = '0';
    cartSubtotal.textContent = '$0';
    cartLineItems.innerHTML = '';
    cartEmptyState.hidden = false;
    proceedButton.disabled = true;
    return;
  }

  cartCount.textContent = String(state.cart.quantity);
  cartSubtotal.textContent = dollars(cartTotal());
  cartEmptyState.hidden = true;
  proceedButton.disabled = false;
  cartLineItems.innerHTML = `
    <div class="cart-line">
      <div>
        <strong>Everyday Mart Digital Gift Card</strong>
        <span>${state.cart.quantity} x ${dollars(state.cart.amount)}</span>
      </div>
      <strong>${dollars(cartTotal())}</strong>
    </div>
  `;
}

function openCart(message = '') {
  const cartDrawer = document.querySelector('#cartDrawer');
  const status = document.querySelector('#cartDrawerStatus');
  cartDrawer.classList.add('is-open');
  if (message) status.textContent = message;
}

function closeCart() {
  document.querySelector('#cartDrawer').classList.remove('is-open');
}

function addToCart() {
  updateProductSubtotal();
  state.cart = {
    amount: state.amount,
    quantity: state.quantity,
  };
  state.checkoutStarted = false;
  document.querySelector('#checkoutStep').hidden = true;
  document.querySelector('#orderConfirmation').hidden = true;
  renderCart();
  openCart(`${state.quantity} item${state.quantity > 1 ? 's' : ''} added to cart.`);
}

function proceedToCheckout() {
  if (!state.cart) {
    openCart('Add a gift card before checkout.');
    return false;
  }
  state.checkoutStarted = true;
  document.querySelector('#checkoutStep').hidden = false;
  document.querySelector('#orderConfirmation').hidden = true;
  openCart('Checkout is ready. Add recipient details below.');
  return true;
}

function validateCheckoutForm() {
  const name = document.querySelector('#recipientName').value.trim();
  const email = document.querySelector('#recipientEmail').value.trim();
  const emailLooksValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  if (!state.cart) return 'Add a gift card before checkout.';
  if (!name || !email) return 'Enter recipient details before placing the order.';
  if (!emailLooksValid) return 'Enter a valid recipient email before checkout.';
  return '';
}

function orderId() {
  return `EM-${String(cartTotal() + state.cart.quantity * 37).padStart(6, '0').slice(-6)}`;
}

function deliverySummary() {
  const deliveryTiming = document.querySelector('#deliveryTiming');
  return DELIVERY_LABELS[deliveryTiming.value] || deliveryTiming.options[deliveryTiming.selectedIndex].text.toLowerCase();
}

function placeOrder(event) {
  if (event) event.preventDefault();
  const status = document.querySelector('#cartDrawerStatus');
  const error = validateCheckoutForm();
  if (error) {
    status.textContent = error;
    return false;
  }

  const confirmation = document.querySelector('#orderConfirmation');
  const confirmationText = document.querySelector('#orderConfirmationText');
  const orderNumber = document.querySelector('#orderNumber');
  const id = orderId();
  const total = dollars(cartTotal());
  const timing = deliverySummary();

  orderNumber.textContent = id;
  confirmationText.textContent = `${total} digital gift card order for ${document.querySelector('#recipientEmail').value.trim()} is confirmed, ${timing}.`;
  confirmation.hidden = false;
  status.textContent = `Order ${id} confirmed.`;
  closeCart();
  return true;
}

function continueShopping() {
  state.cart = null;
  state.checkoutStarted = false;
  renderCart();
  document.querySelector('#checkoutStep').hidden = true;
  document.querySelector('#orderConfirmation').hidden = true;
  document.querySelector('#cartDrawerStatus').textContent = 'Your cart is empty.';
}

function filterReviews() {
  const filter = document.querySelector('#reviewFilter').value;
  for (const card of document.querySelectorAll('[data-review-category]')) {
    const visible = filter === 'all' || card.dataset.reviewCategory === filter;
    card.hidden = !visible;
  }
}

for (const input of document.querySelectorAll('input[name="amount"]')) {
  input.addEventListener('change', () => {
    syncDenominationControls(Number(input.value));
    updateProductSubtotal();
  });
}

for (const id of ['amountSelect', 'quantityInput']) {
  const control = document.querySelector(`#${id}`);
  control.addEventListener('input', updateProductSubtotal);
  control.addEventListener('change', updateProductSubtotal);
}

document.querySelector('#addToCartButton').addEventListener('click', addToCart);
document.querySelector('#cartButton').addEventListener('click', () => openCart(state.cart ? 'Cart opened.' : 'Your cart is empty.'));
document.querySelector('#closeCartButton').addEventListener('click', closeCart);
document.querySelector('#proceedCheckoutButton').addEventListener('click', proceedToCheckout);
document.querySelector('#checkoutForm').addEventListener('submit', placeOrder);
document.querySelector('#continueShoppingButton').addEventListener('click', continueShopping);
document.querySelector('#reviewFilter').addEventListener('change', filterReviews);

syncDenominationControls(state.amount);
updateProductSubtotal();
renderCart();
