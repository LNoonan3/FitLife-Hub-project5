document.addEventListener('DOMContentLoaded', function() {
  if (typeof STRIPE_PUBLIC_KEY === 'undefined') return;

  const stripe = Stripe(STRIPE_PUBLIC_KEY);
  const elements = stripe.elements();
  const card = elements.create('card');
  card.mount('#card-element');

  card.on('change', function(event) {
    document.getElementById('card-errors').textContent = event.error ? event.error.message : '';
  });

  function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-4`;
    toast.role = "alert";
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }

  const form = document.getElementById('checkout-form');
  if (form) {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      const payBtn = document.getElementById('pay-btn');
      const payBtnText = document.getElementById('pay-btn-text');
      const payBtnSpinner = document.getElementById('pay-btn-spinner');
      payBtn.disabled = true;
      payBtnText.textContent = "Processing...";
      payBtnSpinner.classList.remove('d-none');

      const formData = new FormData(form);
      const response = await fetch(CREATE_PAYMENT_INTENT_URL, {
        method: "POST",
        headers: {
          "X-CSRFToken": formData.get('csrfmiddlewaretoken'),
        },
        body: formData
      });
      const data = await response.json();

      if (data.error) {
        showToast("Payment failed: " + data.error, "danger");
        document.getElementById('card-errors').textContent = data.error;
        payBtn.disabled = false;
        payBtnText.textContent = "Confirm & Pay";
        payBtnSpinner.classList.add('d-none');
        return;
      }

      const { clientSecret } = data;

      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: card,
          billing_details: {
            name: formData.get('full_name'),
            email: USER_EMAIL,
            address: {
              line1: formData.get('address'),
              city: formData.get('city'),
              postal_code: formData.get('postcode'),
              country: formData.get('country')
            }
          }
        }
      });

      if (result.error) {
        showToast("Payment failed: " + result.error.message, "danger");
        document.getElementById('card-errors').textContent = result.error.message;
        payBtn.disabled = false;
        payBtnText.textContent = "Confirm & Pay";
        payBtnSpinner.classList.add('d-none');
      } else {
        if (result.paymentIntent.status === 'succeeded') {
          showToast("Your purchase was successful! Thank you for your order.", "success");
          // Clear the cart in the backend
          fetch(CART_CLEAR_URL, {
            method: "POST",
            headers: {
              "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            }
          });

          // Clear the order summary table
          const orderSummary = document.querySelector('.checkout-table tbody');
          if (orderSummary) {
            orderSummary.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Your cart is now empty.</td></tr>';
          }
          // Clear the grand total
          const grandTotal = document.querySelector('.checkout-table tfoot .text-primary');
          if (grandTotal) {
            grandTotal.textContent = "€0.00";
          }

          // Hide or reset the payment form
          form.reset();
          form.querySelectorAll('input, button').forEach(el => el.disabled = true);
          payBtnText.textContent = "Paid";
          payBtnSpinner.classList.add('d-none');
        }
      }
      payBtn.disabled = false;
    });
  }
});