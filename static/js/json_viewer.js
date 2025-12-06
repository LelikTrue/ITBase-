document.addEventListener('DOMContentLoaded', function() {
    const jsonModalEl = document.getElementById('jsonViewerModal');
    if (!jsonModalEl) return;

    const jsonModal = new bootstrap.Modal(jsonModalEl);
    const container = document.getElementById('jsonViewerContent');

    // Syntax Highlight Function
    function syntaxHighlight(json) {
        if (typeof json !== 'string') {
            json = JSON.stringify(json, undefined, 2);
        }
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }

    // Event Delegation for dynamic tables
    document.body.addEventListener('click', function(e) {
        const btn = e.target.closest('.view-json-btn');
        if (btn) {
            e.preventDefault();
            const rawData = btn.getAttribute('data-json');
            try {
                const jsonObj = JSON.parse(rawData);
                container.innerHTML = syntaxHighlight(jsonObj);
                jsonModal.show();
            } catch (err) {
                container.textContent = 'Invalid JSON data: ' + err.message;
                jsonModal.show();
            }
        }
    });
});
