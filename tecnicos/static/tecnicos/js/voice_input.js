/**
 * Voice input - activa reconocimiento de voz en campos de formulario.
 * Agrega un botón de micrófono junto a cada input/textarea marcado.
 */
const VoiceInput = (function () {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    function isSupported() {
        return !!SpeechRecognition;
    }

    function createMicButton() {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline-secondary btn-mic';
        btn.title = 'Dictar con voz';
        btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
        btn.style.cssText = 'min-width:42px;';
        return btn;
    }

    function attachToField(field) {
        if (!isSupported()) return;
        if (field.dataset.micAttached) return;
        field.dataset.micAttached = '1';

        // Envolver el campo en un input-group si no lo está
        const parent = field.parentNode;
        let wrapper = parent;

        if (!parent.classList.contains('input-group')) {
            wrapper = document.createElement('div');
            wrapper.className = 'd-flex gap-1 align-items-start';
            parent.insertBefore(wrapper, field);
            wrapper.appendChild(field);
        }

        const btn = createMicButton();
        wrapper.appendChild(btn);

        const recognition = new SpeechRecognition();
        recognition.lang = 'es-CL';
        recognition.continuous = false;
        recognition.interimResults = false;

        let active = false;

        btn.addEventListener('click', function () {
            if (active) {
                recognition.stop();
                return;
            }
            recognition.start();
        });

        recognition.onstart = function () {
            active = true;
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-danger');
            btn.innerHTML = '<i class="bi bi-mic-fill"></i> <span style="font-size:0.7rem">Escuchando...</span>';
            btn.title = 'Detener';
        };

        recognition.onresult = function (e) {
            const texto = e.results[0][0].transcript;
            // Agregar al texto existente si el campo ya tiene contenido
            if (field.value && field.value.slice(-1) !== ' ') {
                field.value += ' ' + texto;
            } else {
                field.value += texto;
            }
            field.dispatchEvent(new Event('input'));
        };

        recognition.onend = function () {
            active = false;
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-outline-secondary');
            btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
            btn.title = 'Dictar con voz';
        };

        recognition.onerror = function (e) {
            active = false;
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-outline-secondary');
            btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
            if (e.error === 'not-allowed') {
                alert('Permiso de micrófono denegado. Active el micrófono en su navegador.');
            }
        };
    }

    function initAll() {
        if (!isSupported()) {
            console.warn('VoiceInput: Web Speech API no disponible en este navegador.');
            return;
        }
        // Aplicar a todos los inputs de texto y textareas en formularios
        document.querySelectorAll(
            'form input[type="text"], form input[type="email"], form input[type="number"], form textarea'
        ).forEach(attachToField);
    }

    return { initAll, attachToField, isSupported };
})();

document.addEventListener('DOMContentLoaded', function () {
    VoiceInput.initAll();
});
