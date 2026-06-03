(function () {
  const dataEl = document.getElementById('upload-notes-bookings');
  const select = document.getElementById('booking-select');
  const form = document.getElementById('upload-notes-form');
  if (!dataEl || !select || !form) return;

  const bookings = JSON.parse(dataEl.textContent);
  const panel = document.getElementById('upload-notes-panel');
  const badgesEl = document.getElementById('existing-files');
  const zone = document.getElementById('upload-dropzone');
  const input = document.getElementById('upload-files');
  const listEl = document.getElementById('selected-files');
  const btn = document.getElementById('upload-submit');

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function iconFor(ext) {
    if (ext === 'pdf') return '📄';
    if (ext === 'xlsx' || ext === 'xls') return '📊';
    if (ext === 'doc' || ext === 'docx') return '📝';
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return '🖼️';
    return '📎';
  }

  function renderSelected() {
    listEl.innerHTML = '';
    Array.from(input.files).forEach(function (f) {
      const row = document.createElement('div');
      row.className = 'dropzone__file-row';
      row.innerHTML =
        '<span>' + iconFor(f.name.split('.').pop().toLowerCase()) + '</span>' +
        '<span class="dropzone__file-name">' + f.name + '</span>' +
        '<span class="dropzone__file-size">' + formatBytes(f.size) + '</span>';
      listEl.appendChild(row);
    });
    btn.disabled = input.files.length === 0;
  }

  function clearFiles() {
    input.value = '';
    listEl.innerHTML = '';
    btn.disabled = true;
  }

  function renderBadges(files) {
    badgesEl.innerHTML = '';
    if (!files.length) {
      badgesEl.hidden = true;
      return;
    }
    files.forEach(function (file) {
      const item = document.createElement('div');
      item.className = 'file-badges__item';
      item.textContent = iconFor(file.ext) + ' ' + file.name;
      badgesEl.appendChild(item);
    });
    badgesEl.hidden = false;
  }

  function selectBooking(name) {
    const booking = bookings.find(function (b) { return b.name === name; });
    if (!booking) {
      panel.hidden = true;
      return;
    }

    form.action = '/upload-notes/' + encodeURIComponent(booking.name);
    btn.textContent = '⬆ Upload to ' + booking.name;
    renderBadges(booking.files);
    clearFiles();
    panel.hidden = false;
  }

  select.addEventListener('change', function () {
    selectBooking(select.value);
  });

  input.addEventListener('change', renderSelected);

  zone.addEventListener('dragover', function (e) {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', function () {
    zone.classList.remove('drag-over');
  });
  zone.addEventListener('drop', function (e) {
    e.preventDefault();
    zone.classList.remove('drag-over');
    input.files = e.dataTransfer.files;
    renderSelected();
  });
}());
