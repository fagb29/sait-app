/**
 * Validador de cámara para formularios de inspección.
 * Fuerza captura directa desde cámara (sin galería en móvil),
 * exige geolocalización en tiempo real y rechaza fotos negras/oscuras.
 */
const CameraValidator = (function () {
    const MIN_BRIGHTNESS = 35; // 0–255: rechazar si el promedio está bajo este umbral

    function isMobile() {
        return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    }

    function getGeolocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Este dispositivo no tiene GPS disponible.'));
                return;
            }
            navigator.geolocation.getCurrentPosition(
                pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                () => reject(new Error('No se pudo obtener la ubicación. Active el GPS y los permisos de ubicación.')),
                { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
            );
        });
    }

    function checkBrightness(imageFile) {
        return new Promise(resolve => {
            const img = new Image();
            const url = URL.createObjectURL(imageFile);
            img.onload = function () {
                const canvas = document.createElement('canvas');
                // Reducir resolución para análisis rápido
                canvas.width = 200;
                canvas.height = 200;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, 200, 200);
                const { data } = ctx.getImageData(0, 0, 200, 200);
                let total = 0;
                const pixels = data.length / 4;
                for (let i = 0; i < data.length; i += 4) {
                    total += (data[i] + data[i + 1] + data[i + 2]) / 3;
                }
                URL.revokeObjectURL(url);
                resolve((total / pixels) >= MIN_BRIGHTNESS);
            };
            img.onerror = () => { URL.revokeObjectURL(url); resolve(false); };
            img.src = url;
        });
    }

    function setStatus(el, msg, type) {
        el.className = `alert alert-${type} mt-2 py-2`;
        el.innerHTML = msg;
        el.classList.remove('d-none');
    }

    function buildMapLink(lat, lng) {
        const now = new Date();
        const hora = now.toLocaleTimeString('es-CL');
        const fecha = now.toLocaleDateString('es-CL');
        const url = `https://maps.google.com/?q=${lat},${lng}`;
        return `<br><small><i class="bi bi-clock"></i> <b>Hora:</b> ${fecha} ${hora} &nbsp;|&nbsp;
            <a href="${url}" target="_blank" rel="noopener">
                <i class="bi bi-geo-alt-fill"></i> Confirmar ubicación en Maps
            </a></small>`;
    }

    // ─── Modo MÓVIL: cámara en vivo con getUserMedia ────────────────────────────
    function buildMobileUI(fileInput, latInput, lngInput) {
        fileInput.style.display = 'none';

        const wrapper = document.createElement('div');
        wrapper.className = 'camera-validator-wrapper';

        const btnTomar = document.createElement('button');
        btnTomar.type = 'button';
        btnTomar.className = 'btn btn-primary btn-lg w-100 mb-2';
        btnTomar.innerHTML = '<i class="bi bi-camera-fill me-2"></i>Tomar Foto desde Cámara';

        const previewWrap = document.createElement('div');
        previewWrap.className = 'd-none';

        const video = document.createElement('video');
        video.autoplay = true;
        video.playsInline = true;
        video.muted = true;
        video.style.cssText = 'width:100%;max-height:320px;border-radius:8px;background:#000;';

        const btnCapturar = document.createElement('button');
        btnCapturar.type = 'button';
        btnCapturar.className = 'btn btn-success btn-lg w-100 mt-2';
        btnCapturar.innerHTML = '<i class="bi bi-camera me-2"></i>Capturar Foto';

        const btnCancelar = document.createElement('button');
        btnCancelar.type = 'button';
        btnCancelar.className = 'btn btn-outline-secondary w-100 mt-1';
        btnCancelar.textContent = 'Cancelar';

        previewWrap.append(video, btnCapturar, btnCancelar);

        const listaFotos = document.createElement('div');
        listaFotos.className = 'lista-fotos mt-2';

        const statusEl = document.createElement('div');
        statusEl.className = 'd-none';

        wrapper.append(btnTomar, previewWrap, listaFotos, statusEl);
        fileInput.parentNode.insertBefore(wrapper, fileInput);

        let stream = null;
        let capturedFiles = [];

        function syncFileInput() {
            const dt = new DataTransfer();
            capturedFiles.forEach(f => dt.items.add(f));
            fileInput.files = dt.files;
        }

        function renderFotos() {
            listaFotos.innerHTML = '';
            capturedFiles.forEach((file, idx) => {
                const url = URL.createObjectURL(file);
                const row = document.createElement('div');
                row.className = 'p-2 mb-1 border rounded d-flex align-items-center gap-2';
                row.innerHTML = `
                    <img src="${url}" style="width:56px;height:56px;object-fit:cover;border-radius:6px;">
                    <span class="text-success fw-bold"><i class="bi bi-check-circle-fill"></i> Foto ${idx + 1} — con GPS</span>
                    <button type="button" class="btn btn-sm btn-outline-danger ms-auto eliminar-foto" data-idx="${idx}">
                        <i class="bi bi-trash"></i>
                    </button>`;
                row.querySelector('.eliminar-foto').addEventListener('click', () => {
                    capturedFiles.splice(idx, 1);
                    syncFileInput();
                    renderFotos();
                });
                listaFotos.appendChild(row);
            });
        }

        function cerrarCamara() {
            if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
            video.srcObject = null;
            previewWrap.classList.add('d-none');
            btnTomar.classList.remove('d-none');
        }

        btnTomar.addEventListener('click', async function () {
            btnTomar.disabled = true;
            setStatus(statusEl, '<i class="bi bi-geo-alt-fill"></i> Obteniendo ubicación GPS…', 'info');

            try {
                const coords = await getGeolocation();
                latInput.value = coords.lat;
                lngInput.value = coords.lng;
                setStatus(statusEl,
                    `<i class="bi bi-geo-alt-fill text-success"></i> GPS obtenido: <strong>${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}</strong>${buildMapLink(coords.lat, coords.lng)}`,
                    'success');
            } catch (err) {
                setStatus(statusEl, `<i class="bi bi-exclamation-triangle-fill"></i> <strong>ERROR GPS:</strong> ${err.message}`, 'danger');
                btnTomar.disabled = false;
                return;
            }

            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }
                });
                video.srcObject = stream;
                previewWrap.classList.remove('d-none');
                btnTomar.classList.add('d-none');
            } catch {
                setStatus(statusEl, '<i class="bi bi-camera-video-off"></i> No se pudo acceder a la cámara. Verifique los permisos.', 'danger');
            }
            btnTomar.disabled = false;
        });

        btnCapturar.addEventListener('click', function () {
            if (!video.videoWidth) return;
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);

            canvas.toBlob(async function (blob) {
                const file = new File([blob], `inspeccion_${Date.now()}.jpg`, { type: 'image/jpeg' });

                const ok = await checkBrightness(file);
                if (!ok) {
                    setStatus(statusEl,
                        '<i class="bi bi-moon-stars-fill"></i> <strong>Foto rechazada:</strong> La imagen está demasiado oscura o negra. Mejore la iluminación e intente nuevamente.',
                        'warning');
                    return;
                }

                capturedFiles.push(file);
                syncFileInput();
                renderFotos();
                cerrarCamara();

                setStatus(statusEl,
                    `<i class="bi bi-check-circle-fill text-success"></i> <strong>Foto ${capturedFiles.length} capturada</strong> con GPS y validación de imagen correcta.`,
                    'success');
                btnTomar.innerHTML = '<i class="bi bi-camera-fill me-2"></i>Tomar otra foto';
                btnTomar.classList.remove('d-none');
            }, 'image/jpeg', 0.92);
        });

        btnCancelar.addEventListener('click', cerrarCamara);
    }

    // ─── Modo ESCRITORIO: input de archivo con validación de brillo y geo ───────
    function buildDesktopUI(fileInput, latInput, lngInput) {
        const statusEl = document.createElement('div');
        statusEl.className = 'd-none';
        fileInput.parentNode.insertBefore(statusEl, fileInput.nextSibling);

        // Capturar geo al cargar la página
        setStatus(statusEl, '<i class="bi bi-geo-alt"></i> Obteniendo ubicación GPS…', 'info');
        getGeolocation()
            .then(coords => {
                latInput.value = coords.lat;
                lngInput.value = coords.lng;
                setStatus(statusEl,
                    `<i class="bi bi-geo-alt-fill text-success"></i> Ubicación GPS registrada: <strong>${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}</strong>${buildMapLink(coords.lat, coords.lng)}`,
                    'success');
            })
            .catch(err => {
                setStatus(statusEl, `<i class="bi bi-exclamation-triangle-fill"></i> Advertencia GPS: ${err.message}`, 'warning');
            });

        fileInput.addEventListener('change', async function () {
            const files = Array.from(fileInput.files);
            if (!files.length) return;

            setStatus(statusEl, '<i class="bi bi-hourglass-split"></i> Validando imágenes…', 'info');
            const dt = new DataTransfer();
            let rechazadas = 0;

            for (const file of files) {
                if (await checkBrightness(file)) {
                    dt.items.add(file);
                } else {
                    rechazadas++;
                }
            }

            fileInput.files = dt.files;

            if (rechazadas > 0) {
                setStatus(statusEl,
                    `<i class="bi bi-moon-stars-fill"></i> <strong>${rechazadas} foto(s) rechazada(s)</strong> por estar muy oscuras. Se conservaron ${dt.files.length} foto(s) válidas.`,
                    'warning');
            } else {
                setStatus(statusEl,
                    `<i class="bi bi-check-circle-fill text-success"></i> ${dt.files.length} foto(s) validada(s) correctamente.`,
                    'success');
            }
        });
    }

    // ─── API pública ─────────────────────────────────────────────────────────────
    function init(fileInputId, latInputId, lngInputId) {
        const fileInput = document.getElementById(fileInputId);
        const latInput = document.getElementById(latInputId);
        const lngInput = document.getElementById(lngInputId);
        if (!fileInput || !latInput || !lngInput) return;

        if (isMobile()) {
            buildMobileUI(fileInput, latInput, lngInput);
        } else {
            buildDesktopUI(fileInput, latInput, lngInput);
        }
    }

    // Inicializar todos los inputs marcados con data-camera-validate
    function initAll(latInputId, lngInputId) {
        document.querySelectorAll('[data-camera-validate]').forEach(input => {
            init(input.id, latInputId, lngInputId);
        });
    }

    return { init, initAll };
})();
