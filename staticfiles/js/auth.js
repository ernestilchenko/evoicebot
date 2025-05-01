document.addEventListener('DOMContentLoaded', function () {
    // Form validation
    const forms = document.querySelectorAll('.auth-form');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('.form-control');

        // Handle input focus effects
        inputs.forEach(input => {
            // Add focused class to parent on focus
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('input-focused');
            });

            // Remove focused class on blur if empty
            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('input-focused');
            });
        });

        // Form submission validation
        form.addEventListener('submit', function (e) {
            let hasError = false;

            // Reset previous errors
            const errorMessages = form.querySelectorAll('.error-message');
            errorMessages.forEach(el => el.remove());

            inputs.forEach(input => {
                input.classList.remove('error-input');

                // Required field validation
                if (input.hasAttribute('required') && !input.value.trim()) {
                    e.preventDefault();
                    hasError = true;
                    showError(input, 'To pole jest wymagane');
                }

                // Email validation
                if (input.type === 'email' && input.value.trim()) {
                    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailPattern.test(input.value)) {
                        e.preventDefault();
                        hasError = true;
                        showError(input, 'Wprowadź poprawny adres email');
                    }
                }

                // Password validation
                if (input.name === 'password' && input.value.trim()) {
                    if (input.value.length < 8) {
                        e.preventDefault();
                        hasError = true;
                        showError(input, 'Hasło musi mieć co najmniej 8 znaków');
                    }
                }

                // Password confirmation validation
                if (input.name === 'confirm_password') {
                    const passwordInput = form.querySelector('input[name="password"]');
                    if (passwordInput && input.value !== passwordInput.value) {
                        e.preventDefault();
                        hasError = true;
                        showError(input, 'Hasła nie są identyczne');
                    }
                }
            });

            // Terms checkbox validation (for registration)
            const termsCheckbox = form.querySelector('input[name="terms"]');
            if (termsCheckbox && !termsCheckbox.checked) {
                e.preventDefault();
                hasError = true;
                const checkboxWrapper = termsCheckbox.closest('.checkbox-wrapper');
                const errorElement = document.createElement('div');
                errorElement.className = 'error-message';
                errorElement.textContent = 'Musisz zaakceptować warunki';
                checkboxWrapper.appendChild(errorElement);
            }

            // Show form-level error if there are validation errors
            if (hasError) {
                const formError = document.createElement('div');
                formError.className = 'error-message form-error';
                formError.textContent = 'Popraw błędy w formularzu';
                form.prepend(formError);

                // Scroll to first error
                const firstError = form.querySelector('.error-input') || form.querySelector('.error-message');
                if (firstError) {
                    firstError.scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            }
        });
    });

    // Handle messages auto-close
    const messages = document.querySelectorAll('.message');
    if (messages.length > 0) {
        messages.forEach(message => {
            // Animate the message
            message.style.animation = 'slideIn 0.3s forwards';

            // Auto-close after 5 seconds
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transform = 'translateX(30px)';
                message.style.transition = 'all 0.3s ease';

                setTimeout(() => {
                    message.remove();
                }, 300);
            }, 5000);
        });
    }

    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function () {
            const passwordInput = this.previousElementSibling;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Toggle icon
            this.innerHTML = type === 'password'
                ? '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
                : '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';
        });
    });

    // Helper functions
    function showError(input, message) {
        input.classList.add('error-input');
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> ${message}`;
        input.parentElement.appendChild(errorElement);

        // Clear error on input
        input.addEventListener('input', function () {
            this.classList.remove('error-input');
            const errorMsg = this.parentElement.querySelector('.error-message');
            if (errorMsg) {
                errorMsg.remove();
            }
        }, {once: true});
    }

    // Apply particle background
    createParticles();
});

function createParticles() {
    const container = document.querySelector('.auth-container');
    if (!container) return;

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('span');
        particle.className = 'particle';

        // Random properties
        const size = Math.random() * 5 + 1;
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        const opacity = Math.random() * 0.5 + 0.1;
        const animDuration = Math.random() * 20 + 10;
        const animDelay = Math.random() * 10;

        // Apply styles
        particle.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      background: ${Math.random() > 0.5 ? 'rgba(99, 102, 241, ' + opacity + ')' : 'rgba(16, 185, 129, ' + opacity + ')'};
      border-radius: 50%;
      top: ${posY}%;
      left: ${posX}%;
      pointer-events: none;
      animation: float ${animDuration}s ease-in-out ${animDelay}s infinite;
    `;

        container.appendChild(particle);
    }
}

// Define the float animation in CSS
const style = document.createElement('style');
style.textContent = `
  @keyframes float {
    0%, 100% {
      transform: translateY(0) translateX(0);
    }
    25% {
      transform: translateY(-20px) translateX(10px);
    }
    50% {
      transform: translateY(-10px) translateX(-10px);
    }
    75% {
      transform: translateY(-30px) translateX(5px);
    }
  }
`;
document.head.appendChild(style);