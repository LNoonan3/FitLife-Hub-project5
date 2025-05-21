// main.js

document.addEventListener('DOMContentLoaded', function() {
  // Show spinner on any form submission with class .with-spinner
  document.querySelectorAll('form.with-spinner').forEach(function(form) {
    form.addEventListener('submit', function() {
      let btn = form.querySelector('button[type="submit"]');
      if (btn) {
        let spinner = document.createElement('span');
        spinner.className = 'spinner-border spinner-border-sm ms-2';
        spinner.setAttribute('role', 'status');
        spinner.setAttribute('aria-hidden', 'true');
        btn.appendChild(spinner);
        btn.disabled = true;
      }
    });
  });

  // Scroll-to-top button behavior (if you add one)
  const scrollBtn = document.getElementById('scroll-to-top');
  if (scrollBtn) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        scrollBtn.classList.remove('d-none');
      } else {
        scrollBtn.classList.add('d-none');
      }
    });
    scrollBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
});
