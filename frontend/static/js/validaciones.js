document.addEventListener('DOMContentLoaded', function() {
    const registroForm = document.getElementById('registroForm');
    const loginForm = document.getElementById('loginForm');

    if (registroForm) {
        const cedulaInput = document.getElementById('id_cedula');
        const correoInput = document.getElementById('id_correo');
        const rolSelect = document.getElementById('id_rol');
        const tarjetaGroup = document.getElementById('tarjeta-profesional-group');
        const certificadoGroup = document.getElementById('certificado-discapacidad-group');
        const whatsappGroup = document.getElementById('telefono-whatsapp-group');
        const tarjetaInput = document.getElementById('id_url_tarjeta_profesional');
        const certificadoInput = document.getElementById('id_url_certificado_discapacidad');
        const cedulaDocInput = document.getElementById('id_cedula_documento');
        const whatsappInput = document.getElementById('id_telefono_whatsapp');

        const emailRegex = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(\.[A-Za-z]{2,})?$/;

        function setHidden(el, hidden) {
            if (!el) return;
            el.classList.toggle('is-hidden', hidden);
        }

        function refreshRolFields() {
            const rol = rolSelect ? rolSelect.value : '';

            const isEnfermero = rol === 'enfermero';
            const isDiscapacitado = rol === 'discapacitado';

            setHidden(tarjetaGroup, !isEnfermero);
            setHidden(whatsappGroup, !isEnfermero);
            setHidden(certificadoGroup, !isDiscapacitado);

            if (tarjetaInput) tarjetaInput.required = isEnfermero;
            if (whatsappInput) whatsappInput.required = isEnfermero;
            if (certificadoInput) certificadoInput.required = isDiscapacitado;
        }

        function hasSelectedFile(input) {
            if (!input) return false;
            if ('files' in input) {
                return Boolean(input.files && input.files.length);
            }
            return Boolean((input.value || '').trim());
        }

        if (cedulaInput) {
            cedulaInput.addEventListener('input', function() {
                this.value = this.value.replace(/[^\d]/g, '');
            });
        }

        if (whatsappInput) {
            whatsappInput.addEventListener('input', function() {
                this.value = this.value.replace(/[^\d]/g, '').slice(0, 10);
            });
        }

        if (rolSelect) {
            refreshRolFields();
            rolSelect.addEventListener('change', refreshRolFields);
        }

        registroForm.addEventListener('submit', function(e) {
            let hasError = false;
            const password = document.getElementById('id_password') ? document.getElementById('id_password').value : '';
            const confirmPassword = document.getElementById('id_confirm_password') ? document.getElementById('id_confirm_password').value : '';
            const correo = correoInput ? correoInput.value.trim() : '';
            const cedula = cedulaInput ? cedulaInput.value.trim() : '';
            const rol = rolSelect ? rolSelect.value : '';

            // Limpiar errores previos
            document.querySelectorAll('.error-client').forEach(el => el.remove());

            if (cedulaInput && cedula && !/^\d{5,20}$/.test(cedula)) {
                showError('id_cedula', 'La cédula debe contener solo números (5 a 20 dígitos).');
                hasError = true;
            }

            if (correoInput && correo && !emailRegex.test(correo)) {
                showError('id_correo', 'El formato del correo no es válido.');
                hasError = true;
            }

            if (cedulaDocInput && (!cedulaDocInput.files || !cedulaDocInput.files.length)) {
                showError('id_cedula_documento', 'Debes adjuntar la cédula escaneada (PDF o imagen).');
                hasError = true;
            }

            // Validar contraseñas
            if (password !== confirmPassword) {
                showError('id_confirm_password', 'Las contraseñas no coinciden.');
                hasError = true;
            }

            const passErrors = [];
            if (password.length < 6) passErrors.push('Mínimo 6 caracteres.');
            if (!/[A-Z]/.test(password)) passErrors.push('Al menos una mayúscula.');
            if (!/\d/.test(password)) passErrors.push('Al menos un número.');
            if (!/[^A-Za-z0-9]/.test(password)) passErrors.push('Al menos un carácter especial.');
            if (passErrors.length) {
                showError('id_password', 'Contraseña inválida: ' + passErrors.join(' '));
                hasError = true;
            }

            if (rol === 'enfermero') {
                if (tarjetaInput && !hasSelectedFile(tarjetaInput)) {
                    showError('id_url_tarjeta_profesional', 'Este campo es obligatorio para el rol enfermero.');
                    hasError = true;
                }
                if (whatsappInput && !whatsappInput.value.trim()) {
                    showError('id_telefono_whatsapp', 'Este campo es obligatorio para el rol enfermero.');
                    hasError = true;
                } else if (whatsappInput && whatsappInput.value.trim() && !/^\d{10}$/.test(whatsappInput.value.trim())) {
                    showError('id_telefono_whatsapp', 'El teléfono debe contener 10 dígitos numéricos.');
                    hasError = true;
                }
            }

            if (rol === 'discapacitado') {
                if (certificadoInput && !hasSelectedFile(certificadoInput)) {
                    showError('id_url_certificado_discapacidad', 'Este campo es obligatorio para el rol discapacitado.');
                    hasError = true;
                }
            }

            if (hasError) {
                e.preventDefault();
            }
        });
    }

    function showError(selector, message) {
        const field = document.querySelector('#' + selector);
        if (!field) return;
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-client';
        errorDiv.style.color = '#c53030';
        errorDiv.style.fontSize = '14px';
        errorDiv.style.marginTop = '5px';
        errorDiv.innerText = message;
        field.parentNode.appendChild(errorDiv);
        field.style.borderColor = '#c53030';
    }
});
