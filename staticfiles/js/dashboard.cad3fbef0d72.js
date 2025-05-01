document.addEventListener('DOMContentLoaded', function() {
  // Handle file input previews
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', function() {
      const preview = this.closest('.form-group').querySelector('.file-preview');
      if (preview && this.files && this.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
          preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
          preview.style.display = 'block';
        }

        reader.readAsDataURL(this.files[0]);

        // Update the file name display
        const fileOverlay = this.closest('.file-input-wrapper').querySelector('.file-overlay span');
        if (fileOverlay) {
          fileOverlay.textContent = this.files[0].name;
        }
      }
    });
  });

  // Handle drag and drop for file uploads
  const fileDropAreas = document.querySelectorAll('.file-input-wrapper');
  if (fileDropAreas.length > 0) {
    fileDropAreas.forEach(area => {
      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, preventDefaults, false);
      });

      function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
      }

      ['dragenter', 'dragover'].forEach(eventName => {
        area.addEventListener(eventName, function() {
          area.classList.add('highlight');
        }, false);
      });

      ['dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, function() {
          area.classList.remove('highlight');
        }, false);
      });

      area.addEventListener('drop', function(e) {
        const fileInput = area.querySelector('input[type="file"]');
        if (fileInput && e.dataTransfer.files.length) {
          fileInput.files = e.dataTransfer.files;

          // Trigger change event manually
          const event = new Event('change', { bubbles: true });
          fileInput.dispatchEvent(event);
        }
      }, false);
    });
  }

  // Copy team UUID to clipboard when clicked
  const teamIdElement = document.querySelector('.team-id');
  if (teamIdElement) {
    teamIdElement.style.cursor = 'pointer';
    teamIdElement.title = 'Kliknij, aby skopiować ID';

    teamIdElement.addEventListener('click', function() {
      const uuid = this.textContent.split(': ')[1];
      navigator.clipboard.writeText(uuid).then(() => {
        // Create a temporary tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = 'Skopiowano do schowka!';
        this.appendChild(tooltip);

        // Remove the tooltip after 2 seconds
        setTimeout(() => {
          tooltip.remove();
        }, 2000);
      });
    });
  }

  // Add animation to dashboard cards and sections
  const cards = document.querySelectorAll('.dashboard-card, .team-item, .project-item, .member-card, .team-card, .project-card, .stats-card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'all 0.3s ease';

    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 100 + (index * 50));
  });

  // Add animation to form container
  const formContainer = document.querySelector('.form-container');
  if (formContainer) {
    formContainer.style.opacity = '0';
    formContainer.style.transform = 'translateY(20px)';
    formContainer.style.transition = 'all 0.3s ease';

    setTimeout(() => {
      formContainer.style.opacity = '1';
      formContainer.style.transform = 'translateY(0)';
    }, 100);
  }

  // Handle dropdown toggles in the dashboard
  const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
  dropdownToggles.forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      const dropdown = this.nextElementSibling;
      dropdown.classList.toggle('show');

      // Close when clicked outside
      document.addEventListener('click', function closeDropdown(e) {
        if (!toggle.contains(e.target) && !dropdown.contains(e.target)) {
          dropdown.classList.remove('show');
          document.removeEventListener('click', closeDropdown);
        }
      });
    });
  });

  // Handle manage team members modal
  const memberModal = document.getElementById('member-modal');
  const openModalButtons = document.querySelectorAll('.open-modal');
  const closeModalButtons = document.querySelectorAll('.close-modal');

  if (memberModal) {
    openModalButtons.forEach(button => {
      button.addEventListener('click', function() {
        memberModal.style.display = 'flex';
        setTimeout(() => {
          memberModal.classList.add('show');
        }, 10);
      });
    });

    closeModalButtons.forEach(button => {
      button.addEventListener('click', function() {
        memberModal.classList.remove('show');
        setTimeout(() => {
          memberModal.style.display = 'none';
        }, 300);
      });
    });

    // Close modal when clicking outside of content
    memberModal.addEventListener('click', function(e) {
      if (e.target === memberModal) {
        memberModal.classList.remove('show');
        setTimeout(() => {
          memberModal.style.display = 'none';
        }, 300);
      }
    });
  }

  // Initialize role change functionality
  const roleSelects = document.querySelectorAll('.role-select');
  roleSelects.forEach(select => {
    select.addEventListener('change', function() {
      const memberId = this.getAttribute('data-member-id');
      const form = document.getElementById('role-form-' + memberId);
      if (form) {
        form.submit();
      }
    });
  });
});