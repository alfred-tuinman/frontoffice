/* ============================================================
   index.js — upload / landing page interactions
   ============================================================ */

(function () {
  'use strict';

  const dropzone   = document.getElementById('dropzone');

    if (!dropzone) return;
  const dropzoneIcon = document.querySelector('.dropzone__icon');
  const fileInput  = document.getElementById('file-input');
  const pill       = document.getElementById('file-pill');
  const pillName   = document.getElementById('pill-name');
  const pillRemove = document.getElementById('pill-remove');
  const submitBtn  = document.getElementById('submit-btn');
  const form       = document.getElementById('upload-form');

  console.log('pill name is ',pillName);

  /* ── Drag & drop ─────────────────────────────────────────── */
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
    console.log('add');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-over');
    console.log('remove');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    console.log('remove drop');
    dropzone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') setFile(file);
  });

  /* ── File input change ───────────────────────────────────── */
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) {
      setFile(fileInput.files[0]);
      //fileInput.style.backgroundColor = 'green';
      fileInput.classList.add('has-file');
      dropzoneIcon.textContent = '✅';
    }
  });

  /* ── Set selected file ───────────────────────────────────── */
  function setFile(file) {
    pillName.textContent = file.name;
    pill.classList.add('visible');
    submitBtn.disabled = false;
  }

  /* ── Remove file ─────────────────────────────────────────── */
  pillRemove.addEventListener('click', () => {
    fileInput.value = '';
    console.log(pillName,pillName.textContent);
    fileInput.classList.remove('has-file');
    dropzoneIcon.textContent = '📄';
    pillName.textContent = '';
    pill.classList.remove('visible');
    submitBtn.disabled = true;
  });

  /* ── Submit loading state ────────────────────────────────── */
  form.addEventListener('submit', () => {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span>Extracting with AI…';
  });
})();
