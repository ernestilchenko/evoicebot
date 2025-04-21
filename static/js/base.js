document.addEventListener('DOMContentLoaded', function () {
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const closeMobileNav = document.querySelector('.close-mobile-nav');
    const mobileNav = document.querySelector('.mobile-nav');
    const html = document.documentElement;
    const body = document.body;

    // Create overlay if it doesn't exist
    let mobileNavOverlay = document.querySelector('.mobile-nav-overlay');
    if (!mobileNavOverlay) {
        mobileNavOverlay = document.createElement('div');
        mobileNavOverlay.className = 'mobile-nav-overlay';
        document.body.appendChild(mobileNavOverlay);
    }

    function openMobileMenu() {
        mobileNav.classList.add('active');
        mobileNavOverlay.classList.add('active');
        html.style.overflow = 'hidden';
        body.style.overflow = 'hidden';
    }

    function closeMobileMenu() {
        mobileNav.classList.remove('active');
        mobileNavOverlay.classList.remove('active');
        html.style.overflow = '';
        body.style.overflow = '';
    }

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', openMobileMenu);
    }

    if (closeMobileNav) {
        closeMobileNav.addEventListener('click', closeMobileMenu);
    }

    if (mobileNavOverlay) {
        mobileNavOverlay.addEventListener('click', closeMobileMenu);
    }

    // Close mobile menu when a mobile nav link is clicked
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (link.getAttribute('href').startsWith('#')) {
                closeMobileMenu();
            }
        });
    });

    // Handle messages auto-close
    const messages = document.querySelectorAll('.message');
    if (messages.length > 0) {
        messages.forEach(message => {
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

    // Scroll animation for sections
    const sections = document.querySelectorAll('.section');

    function checkSections() {
        const triggerBottom = window.innerHeight * 0.85;

        sections.forEach(section => {
            const sectionTop = section.getBoundingClientRect().top;

            if (sectionTop < triggerBottom) {
                section.classList.add('active');
            }
        });
    }

    // Check sections on page load
    checkSections();

    // Check sections on scroll
    window.addEventListener('scroll', checkSections);

    // Create background particles
    createParticles();

    // Handle user menu dropdown on mobile
    const userMenuButton = document.querySelector('.user-menu-button');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    if (userMenuButton && dropdownMenu && window.innerWidth < 768) {
        userMenuButton.addEventListener('click', function (e) {
            e.preventDefault();
            dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', function (e) {
            if (!userMenuButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }

    // Add active class to current nav link
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');

        // Check if the link path matches the current path
        if (linkPath === currentPath || (currentPath === '/' && linkPath === '/' || linkPath === '/index.html')) {
            link.classList.add('active');
        }
    });

    // Handle floating labels for forms
    const formControls = document.querySelectorAll('.form-control');

    formControls.forEach(input => {
        // Check if input already has value
        if (input.value.trim() !== '') {
            const label = input.nextElementSibling;
            if (label && label.classList.contains('form-label')) {
                label.style.top = '-0.5rem';
                label.style.left = '0.75rem';
                label.style.fontSize = '0.75rem';
                label.style.color = 'var(--primary-light)';
                label.style.background = 'rgba(17, 24, 39, 0.9)';
                label.style.padding = '0 0.25rem';
            }
        }

        // Handle focus and blur events
        input.addEventListener('focus', function () {
            const label = this.nextElementSibling;
            if (label && label.classList.contains('form-label')) {
                label.style.top = '-0.5rem';
                label.style.left = '0.75rem';
                label.style.fontSize = '0.75rem';
                label.style.color = 'var(--primary-light)';
                label.style.background = 'rgba(17, 24, 39, 0.9)';
                label.style.padding = '0 0.25rem';
            }
        });

        input.addEventListener('blur', function () {
            const label = this.nextElementSibling;
            if (label && label.classList.contains('form-label') && this.value.trim() === '') {
                label.style.top = '';
                label.style.left = '';
                label.style.fontSize = '';
                label.style.color = '';
                label.style.background = '';
                label.style.padding = '';
            }
        });
    });

    // Handle form submissions - MODIFIED TO EXCLUDE SERVER-SUBMIT FORMS
    const forms = document.querySelectorAll('form:not(.server-submit)');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            // Only prevent default if the form doesn't have a specific action attribute
            if (!form.hasAttribute('action') || form.getAttribute('action').trim() === '') {
                e.preventDefault();

                // Show success message
                const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();

                const message = document.createElement('div');
                message.className = 'message success';
                message.innerHTML = `
          <div class="message-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <p>Formularz został wysłany pomyślnie!</p>
        `;

                messagesContainer.appendChild(message);

                // Auto-close after 5 seconds
                setTimeout(() => {
                    message.style.opacity = '0';
                    message.style.transform = 'translateX(30px)';
                    message.style.transition = 'all 0.3s ease';

                    setTimeout(() => {
                        message.remove();
                    }, 300);
                }, 5000);

                // Reset form
                form.reset();
            }
        });
    });

    // Password toggle functionality
    const passwordToggles = document.querySelectorAll('.password-toggle');
    if (passwordToggles) {
        passwordToggles.forEach(toggle => {
            toggle.addEventListener('click', function () {
                const input = this.previousElementSibling;
                if (input && (input.type === 'password' || input.type === 'text')) {
                    input.type = input.type === 'password' ? 'text' : 'password';

                    // Update icon
                    if (input.type === 'password') {
                        this.innerHTML = `
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            `;
                    } else {
                        this.innerHTML = `
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            `;
                    }
                }
            });
        });
    }

    // Animate testimonials if they exist
    const testimonials = document.querySelectorAll('.testimonial-card');
    if (testimonials.length > 1) {
        let currentSlide = 0;

        setInterval(() => {
            testimonials[currentSlide].style.opacity = '0';
            currentSlide = (currentSlide + 1) % testimonials.length;
            setTimeout(() => {
                testimonials[currentSlide].style.opacity = '1';
            }, 500);
        }, 5000);
    }
});

// Create particles for background effect
function createParticles() {
    const particlesContainer = document.querySelector('.particles-container');
    if (!particlesContainer) return;

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

        particlesContainer.appendChild(particle);
    }
}

// Helper function to create messages container
function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}