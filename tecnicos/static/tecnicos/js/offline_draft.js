/**
 * offline_draft.js
 * Guarda automáticamente los formularios en localStorage y los restaura
 * si el dispositivo queda sin conexión. Al recuperar la red, alerta al usuario.
 */
(function () {
    const DRAFT_KEY = 'sait_draft_' + window.location.pathname;

    // Barra de estado offline
    function crearBarra() {
        const bar = document.createElement('div');
        bar.id = 'offline-bar';
        bar.style.cssText = 'display:none;position:fixed;top:0;left:0;right:0;z-index:9999;' +
            'background:#dc3545;color:#fff;text-align:center;padding:8px 12px;font-weight:bold;font-size:0.95rem;';
        bar.innerHTML = '<i class="bi bi-wifi-off"></i> Sin conexión — Su formulario se está guardando automáticamente como borrador.';
        document.body.prepend(bar);
        return bar;
    }

    function serializeForm(form) {
        const data = {};
        new FormData(form).forEach(function (val, key) {
            // No serializar archivos ni CSRF
            if (key === 'csrfmiddlewaretoken') return;
            data[key] = val;
        });
        return data;
    }

    function guardarBorrador(form) {
        try {
            localStorage.setItem(DRAFT_KEY, JSON.stringify(serializeForm(form)));
        } catch (e) { /* cuota llena, ignorar */ }
    }

    function restaurarBorrador(form) {
        try {
            const raw = localStorage.getItem(DRAFT_KEY);
            if (!raw) return;
            const data = JSON.parse(raw);
            Object.keys(data).forEach(function (key) {
                const el = form.elements[key];
                if (!el) return;
                if (el.type === 'checkbox' || el.type === 'radio') {
                    el.checked = (el.value === data[key]);
                } else if (el.tagName !== 'SELECT') {
                    el.value = data[key];
                }
            });
            const aviso = document.createElement('div');
            aviso.className = 'alert alert-warning alert-dismissible fade show mt-2';
            aviso.innerHTML = '<i class="bi bi-floppy"></i> <strong>Borrador restaurado</strong> — ' +
                'Se recuperaron los datos que estaba completando antes de perder la conexión.' +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
            form.prepend(aviso);
        } catch (e) { /* ignorar */ }
    }

    function limpiarBorrador() {
        localStorage.removeItem(DRAFT_KEY);
    }

    document.addEventListener('DOMContentLoaded', function () {
        const form = document.querySelector('form[method="post"]');
        if (!form) return;

        const bar = crearBarra();

        // Restaurar borrador si existe
        restaurarBorrador(form);

        // Auto-guardar cada 15 segundos y en cada cambio
        let timer = setInterval(function () { guardarBorrador(form); }, 15000);
        form.addEventListener('input', function () { guardarBorrador(form); });
        form.addEventListener('change', function () { guardarBorrador(form); });

        // Limpiar borrador al enviar correctamente
        form.addEventListener('submit', function () {
            clearInterval(timer);
            limpiarBorrador();
        });

        // Detectar cambios de conexión
        function actualizarEstado() {
            if (!navigator.onLine) {
                bar.style.display = 'block';
                document.body.style.paddingTop = '42px';
                guardarBorrador(form);
            } else {
                bar.style.display = 'none';
                document.body.style.paddingTop = '';
                // Notificar que recuperó la conexión
                const ok = document.getElementById('online-ok');
                if (!ok) {
                    const msg = document.createElement('div');
                    msg.id = 'online-ok';
                    msg.className = 'alert alert-success alert-dismissible fade show';
                    msg.style.cssText = 'position:fixed;top:8px;right:8px;z-index:9999;min-width:280px;';
                    msg.innerHTML = '<i class="bi bi-wifi"></i> <strong>Conexión restaurada.</strong> Puede enviar el formulario.' +
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" onclick="this.parentElement.remove()"></button>';
                    document.body.appendChild(msg);
                    setTimeout(function () { if (msg.parentElement) msg.remove(); }, 6000);
                }
            }
        }

        window.addEventListener('online', actualizarEstado);
        window.addEventListener('offline', actualizarEstado);
        actualizarEstado();
    });
})();
