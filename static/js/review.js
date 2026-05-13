/* ============================================================
   review.js — review & confirm form interactions
   ============================================================ */

(function () {
  'use strict';
  
  const saveBtn    = document.getElementById('save-btn');
  const reviewForm = document.getElementById('review-form');

  if (!saveBtn) return;

  /* ── Save / submit ───────────────────────────────────────── */
  saveBtn.addEventListener('click', function () {
    this.disabled = true;
    this.textContent = 'Saving…';
    reviewForm.submit();
  });

  /* ── Existing record lookup ──────────────────────────────── */
  const lookupBtn    = document.getElementById('lookup-btn');
  const lookupInput  = document.getElementById('lookup-input');
  const lookupResult = document.getElementById('lookup-result');
  const hQuotId      = document.getElementById('h_quot_id');
  const hItinId      = document.getElementById('h_itin_id');

  function clearLookup() {
    hQuotId.value = '';
    hItinId.value = '';
    lookupResult.innerHTML = '';
    saveBtn.textContent = 'Save to Database';
  }

  lookupInput.addEventListener('input', clearLookup);

  lookupBtn.addEventListener('click', async () => {
    const id = lookupInput.value.trim();
    if (!id) {
      lookupResult.innerHTML = '<span style="color:var(--mid)">Enter a Quotations_id first.</span>';
      return;
    }

    lookupBtn.disabled = true;
    lookupBtn.textContent = 'Checking…';
    lookupResult.innerHTML = '';

    try {
      const fd = new FormData();
      fd.append('Quotations_id', id);

      // NOTE: token is injected by Jinja2 at render time
      const resp = await fetch(LOOKUP_URL, { method: 'POST', body: fd });
      const data = await resp.json();

      if (data.found) {
        hQuotId.value = data.Quotations_id;
        hItinId.value = data.itineraries_id || '';
        const itinNote = data.itineraries_id
          ? `itineraries #${data.itineraries_id}`
          : 'no itinerary row yet';
        lookupResult.innerHTML =
          `<span style="color:var(--green)">✅ Found: <strong>${data.PrincipalClient}</strong> ` +
          `(Ref: ${data.QuotationRef}) — ${itinNote}. ` +
          `Submitting will <strong>UPDATE</strong> these records.</span>`;
        saveBtn.textContent = 'Update Database';
      } else {
        hQuotId.value = '';
        hItinId.value = '';
        lookupResult.innerHTML =
          `<span style="color:var(--red)">⚠ No record found for Quotations_id ${id}. ` +
          `A new record will be created.</span>`;
        saveBtn.textContent = 'Save to Database';
      }
    } catch (err) {
      lookupResult.innerHTML = '<span style="color:var(--red)">⚠ Could not reach server.</span>';
      console.error('Lookup error:', err);
    } finally {
      lookupBtn.disabled = false;
      lookupBtn.textContent = 'Check DB';
    }
  });
})();
