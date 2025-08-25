document.addEventListener('DOMContentLoaded', function() {
  if (typeof STRIPE_PUBLIC_KEY === 'undefined') return;

  const stripe = Stripe(STRIPE_PUBLIC_KEY);
  const elements = stripe.elements();
  const card = elements.create('card');
  card.mount('#card-element');

  card.on('change', function(event) {
    document.getElementById('card-errors').textContent = event.error ? event.error.message : '';
  });

  const form = document.getElementById('subscription-form');
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
      const { paymentMethod, error } = await stripe.createPaymentMethod({
        type: 'card',
        card: card,
        billing_details: {
          name: formData.get('full_name'),
          email: formData.get('email')
        }
      });

      if (error) {
        document.getElementById('card-errors').textContent = error.message;
        payBtn.disabled = false;
        payBtnText.textContent = "Subscribe & Pay";
        payBtnSpinner.classList.add('d-none');
        return;
      }

      formData.append('payment_method_id', paymentMethod.id);

      const response = await fetch(CREATE_SUBSCRIPTION_URL, {
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
        payBtnText.textContent = "Subscribe & Pay";
        payBtnSpinner.classList.add('d-none');
        return;
      }

      const { clientSecret } = data;
      const result = await stripe.confirmCardPayment(clientSecret);

      if (result.error) {
        document.getElementById('card-errors').textContent = result.error.message;
        payBtn.disabled = false;
        payBtnText.textContent = "Subscribe & Pay";
        payBtnSpinner.classList.add('d-none');
      } else {
        if (result.paymentIntent.status === 'succeeded') {
          window.location.href = "/subscriptions/success/";
        }
      }
    });
  }
});