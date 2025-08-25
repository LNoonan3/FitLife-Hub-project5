document.addEventListener('DOMContentLoaded', function() {
  if (typeof STRIPE_PUBLIC_KEY === 'undefined') return;

  const stripe = Stripe(STRIPE_PUBLIC_KEY);
  const elements = stripe.elements();
  const card = elements.create('card');
  card.mount('#card-element');

  card.on('change', function(event) {
    document.getElementById('card-errors').textContent = event.error ? event.error.message : '';
  });

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
        document.getElementById('card-errors').textContent = result.error.message;
        payBtn.disabled = false;
        payBtnText.textContent = "Confirm & Pay";
        payBtnSpinner.classList.add('d-none');
      } else {
        if (result.paymentIntent.status === 'succeeded') {
          window.location.href = CHECKOUT_SUCCESS_URL;
        }
      }
    });
  }
});