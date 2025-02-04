// Form validation
(() => {
    'use strict'
    const forms = document.querySelectorAll('.needs-validation')
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            form.classList.add('was-validated')
        }, false)
    })
})()

// Password visibility toggle
const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#password');

togglePassword.addEventListener('click', function () {
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    this.classList.toggle('bi-eye');
    this.classList.toggle('bi-eye-slash');
});

// Password strength checker
const passwordInput = document.querySelector('#password');
const strengthBar = document.querySelector('#passwordStrength');
const requirements = document.querySelectorAll('.requirement-item i');

passwordInput.addEventListener('input', function () {
    const value = this.value;
    let strength = 0;
    let checks = [
        value.length >= 8,
        /[A-Z]/.test(value),
        /[0-9]/.test(value),
        /[^A-Za-z0-9]/.test(value)
    ];

    checks.forEach((check, index) => {
        if (check) {
            strength += 25;
            requirements[index].classList.remove('bi-circle', 'text-muted');
            requirements[index].classList.add('bi-check-circle-fill', 'text-success');
        } else {
            requirements[index].classList.remove('bi-check-circle-fill', 'text-success');
            requirements[index].classList.add('bi-circle', 'text-muted');
        }
    });

    strengthBar.style.width = strength + '%';

    if (strength <= 25) {
        strengthBar.className = 'progress-bar bg-danger';
    } else if (strength <= 50) {
        strengthBar.className = 'progress-bar bg-warning';
    } else if (strength <= 75) {
        strengthBar.className = 'progress-bar bg-info';
    } else {
        strengthBar.className = 'progress-bar bg-success';
    }
});