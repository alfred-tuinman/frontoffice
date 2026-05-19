if (document.querySelector("#upload-form")) {

  const form = document.querySelector("#upload-form");
  const dropzone = document.querySelector("#dropzone");
  const fileInput = document.querySelector("#file-input");
  const filePill = document.querySelector("#file-pill");
  const pillName = document.querySelector("#pill-name");
  const pillRemove = document.querySelector("#pill-remove");
  const submitBtn = document.querySelector("#submit-btn");
  const errorBox = document.querySelector("#error-box");
  const errorMessage = document.querySelector("#error-message");
  const loadingIndicator = document.querySelector("#loading-indicator");

  let selectedFile = null;

  function setFile(file) {

    if (file.type !== "application/pdf") {
      showError("Please upload a PDF file.");
      return;
    }

    clearError();

    selectedFile = file;

    pillName.textContent = file.name;

    filePill.classList.add("visible");

    submitBtn.disabled = false;
  }

  function clearFile() {

    selectedFile = null;

    fileInput.value = "";

    filePill.classList.remove("visible");

    submitBtn.disabled = true;
  }

  function showError(message) {

    loadingIndicator.style.display = "none";

    errorBox.style.display = "block";

    errorMessage.textContent = `⚠ ${message}`;

    submitBtn.disabled = false;

    submitBtn.innerHTML = "Extract & Review";
  }

  function clearError() {

    errorBox.style.display = "none";

    errorMessage.textContent = "";
  }

  dropzone.addEventListener("dragover", event => {

    event.preventDefault();

    dropzone.classList.add("drag-over");
  });

  dropzone.addEventListener("dragleave", () => {

    dropzone.classList.remove("drag-over");
  });

  dropzone.addEventListener("drop", event => {

    event.preventDefault();

    dropzone.classList.remove("drag-over");

    const file = event.dataTransfer.files[0];

    if (file) {
      setFile(file);
    }
  });

  fileInput.addEventListener("change", event => {

    const file = event.target.files[0];

    if (file) {
      setFile(file);
    }
  });

  pillRemove.addEventListener("click", clearFile);

  form.addEventListener("submit", async event => {

    event.preventDefault();

    if (!selectedFile) return;

    clearError();

    submitBtn.disabled = true;

    loadingIndicator.style.display = "flex";

    submitBtn.innerHTML =
      `<span class="spinner"></span>Extracting with AI…`;

    try {

      const formData = new FormData();

      formData.append("pdf", selectedFile);

      const uploadUrl = form.action;

      const response = await fetch(uploadUrl, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status} for ${uploadUrl}`);
      }

      window.location.href = '/review';

    } catch (error) {

      showError(error.message);

      submitBtn.disabled = false;

      submitBtn.innerHTML = "Extract & Review";
    }
  });

}