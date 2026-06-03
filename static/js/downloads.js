(function () {
  const dataEl = document.getElementById('downloads-bookings');
  const select = document.getElementById('booking-select');
  if (!dataEl || !select) return;

  const bookings = JSON.parse(dataEl.textContent);
  const panel = document.getElementById('downloads-panel');
  const listEl = document.getElementById('downloads-file-list');

  function iconFor(ext) {
    if (ext === 'pdf') return '📄';
    if (ext === 'xlsx' || ext === 'xls') return '📊';
    if (ext === 'doc' || ext === 'docx') return '📝';
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return '🖼️';
    return '📎';
  }

  function renderFiles(booking) {
    listEl.innerHTML = '';

    if (!booking.files.length) {
      const empty = document.createElement('p');
      empty.className = 'file-item__empty';
      empty.textContent = 'No files found';
      listEl.appendChild(empty);
      return;
    }

    booking.files.forEach(function (file) {
      const row = document.createElement('div');
      row.className = 'file-item';
      const url =
        '/download/' +
        encodeURIComponent(booking.name) +
        '/' +
        encodeURIComponent(file.name);
      row.innerHTML =
        '<span class="file-item__icon">' + iconFor(file.ext) + '</span>' +
        '<span class="file-item__name"></span>' +
        '<span class="file-item__size"></span>' +
        '<a class="btn btn--download" href="">⬇ Download</a>';
      row.querySelector('.file-item__name').textContent = file.name;
      row.querySelector('.file-item__size').textContent = file.size;
      row.querySelector('a').href = url;
      listEl.appendChild(row);
    });
  }

  select.addEventListener('change', function () {
    const booking = bookings.find(function (b) {
      return b.name === select.value;
    });
    if (!booking) {
      panel.hidden = true;
      return;
    }
    renderFiles(booking);
    panel.hidden = false;
  });
}());
