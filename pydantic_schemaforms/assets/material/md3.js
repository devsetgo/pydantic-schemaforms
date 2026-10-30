(function () {
    'use strict';
    if (window.schemaformsMaterial) {
        return;
    }
    window.schemaformsMaterial = true;

    function syncSlider(input) {
        var min = parseFloat(input.min) || 0;
        var max = input.max === '' ? 100 : parseFloat(input.max);
        var value = parseFloat(input.value) || 0;
        var progress = max > min ? ((value - min) / (max - min)) * 100 : 0;
        input.style.setProperty('--md-slider-progress', progress + '%');
    }

    function init() {
        document.querySelectorAll('form.md-form').forEach(function (form) {
            if (form.dataset.mdReady) {
                return;
            }
            form.dataset.mdReady = 'true';
            form.querySelectorAll('input[type="range"]').forEach(syncSlider);
            form.addEventListener('input', function (event) {
                if (event.target.type === 'range') {
                    syncSlider(event.target);
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
