document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const themeIcon = document.querySelector("[data-theme-icon]");
  const applyTheme = (theme) => {
    const isLight = theme === "light";
    document.body.classList.toggle("acadeval-light", isLight);
    document.body.classList.toggle("acadeval-dark", !isLight);
    if (themeToggle) {
      themeToggle.setAttribute("aria-label", isLight ? "Switch to dark mode" : "Switch to light mode");
      themeToggle.setAttribute("title", isLight ? "Switch to dark mode" : "Switch to light mode");
    }
    if (themeIcon) themeIcon.textContent = isLight ? "☀" : "☾";
  };
  applyTheme(localStorage.getItem("acadeval-theme") || "dark");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const nextTheme = document.body.classList.contains("acadeval-light") ? "dark" : "light";
      localStorage.setItem("acadeval-theme", nextTheme);
      applyTheme(nextTheme);
    });
  }

  const alerts = document.querySelectorAll(".toast-stack .alert");
  alerts.forEach((alert) => {
    window.setTimeout(() => {
      alert.classList.remove("show");
    }, 5000);
  });
});

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-code]");
  if (!button) return;
  const block = button.closest("[data-code-block]");
  const code = block ? block.querySelector("code") : null;
  if (!code) return;
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText(code.textContent);
    button.textContent = "Copied";
  } catch (error) {
    const textarea = document.createElement("textarea");
    textarea.value = code.textContent;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
    button.textContent = "Copied";
  }
  window.setTimeout(() => {
    button.textContent = original;
  }, 1800);
});
document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-ai-toggle]");
  if (!toggle) return;
  const widget = toggle.closest("[data-ai-widget]") || document.querySelector("[data-ai-widget]");
  if (widget) widget.classList.toggle("is-open");
});

const escapeHtml = (value) => String(value || "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const linesToParagraphs = (value) => escapeHtml(value)
  .split(/\n{2,}/)
  .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
  .join("");

const tableHtmlFromPipeRows = (value) => {
  const rows = String(value || "")
    .split(/\r?\n/)
    .map((line) => line.split("|").map((cell) => escapeHtml(cell.trim())))
    .filter((cells) => cells.some(Boolean));
  if (!rows.length) return "<p class=\"text-muted\">Table preview will appear here.</p>";
  const [head, ...body] = rows;
  return `<div class="table-responsive article-table"><table class="table table-striped align-middle"><thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead><tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
};

const renderBuilderPreview = (form) => {
  const preview = form.querySelector("[data-live-preview]");
  if (!preview) return;
  const getField = (name) => form.querySelector(`[data-builder-field="${name}"]`)?.value || "";
  const type = getField("type") || "paragraph";
  const title = getField("title");
  const subtitle = getField("subtitle");
  const body = getField("body");
  const table = getField("table");
  const titleHtml = title ? `<h2 class="h4 text-slate">${escapeHtml(title)}</h2>` : "";
  const subtitleHtml = subtitle ? `<p class="lead">${escapeHtml(subtitle)}</p>` : "";
  if (type === "subtitle") {
    preview.innerHTML = `<h2 class="article-subtitle">${escapeHtml(title || body || "Subtitle")}</h2>${subtitleHtml}`;
  } else if (type === "section") {
    preview.innerHTML = `<section class="article-section">${titleHtml}${subtitleHtml}${linesToParagraphs(body || "Section body preview.")}</section>`;
  } else if (type === "code") {
    preview.innerHTML = `<div class="code-block"><pre><code>${escapeHtml(body || "print('Preview')")}</code></pre></div>`;
  } else if (type === "output") {
    preview.innerHTML = `<div class="output-block"><div class="output-heading"><span class="output-icon">&gt;_</span><strong>${escapeHtml(title || "Output")}</strong></div><pre>${escapeHtml(body || "Preview output")}</pre></div>`;
  } else if (type === "table") {
    preview.innerHTML = tableHtmlFromPipeRows(table || "Column A|Column B\nValue A|Value B");
  } else if (type === "tile") {
    preview.innerHTML = `<div class="article-tile">${title ? `<strong>${escapeHtml(title)}</strong>` : ""}${subtitle ? `<span>${escapeHtml(subtitle)}</span>` : ""}${linesToParagraphs(body || "Tile preview.")}</div>`;
  } else if (type === "quote") {
    preview.innerHTML = `<blockquote class="article-quote">${linesToParagraphs(body || "Quote preview.")}${title ? `<cite>${escapeHtml(title)}</cite>` : ""}</blockquote>`;
  } else if (type === "callout") {
    preview.innerHTML = `<div class="article-callout">${title ? `<strong>${escapeHtml(title)}</strong>` : ""}${linesToParagraphs(body || "Callout preview.")}</div>`;
  } else if (type === "screenshot") {
    preview.innerHTML = `<figure class="screenshot-block"><figcaption>${escapeHtml(title || "Screenshot caption")}</figcaption></figure>`;
  } else {
    preview.innerHTML = `<div class="article-paragraph">${titleHtml}${linesToParagraphs(body || "Paragraph preview.")}</div>`;
  }
};

document.querySelectorAll("[data-builder-form]").forEach((form) => {
  renderBuilderPreview(form);
  form.addEventListener("input", () => renderBuilderPreview(form));
  form.addEventListener("change", () => renderBuilderPreview(form));

  const tableButton = form.querySelector("[data-build-table]");
  tableButton?.addEventListener("click", () => {
    const columns = Math.max(1, Math.min(8, Number(form.querySelector("[data-table-columns]")?.value || 3)));
    const rows = Math.max(1, Math.min(20, Number(form.querySelector("[data-table-rows]")?.value || 4)));
    const tableTarget = form.querySelector("[data-table-source]");
    if (!tableTarget) return;
    const header = Array.from({ length: columns }, (_, index) => `Column ${index + 1}`).join("|");
    const bodyRows = Array.from({ length: rows - 1 }, (_, rowIndex) => (
      Array.from({ length: columns }, (_, colIndex) => `Row ${rowIndex + 1} Col ${colIndex + 1}`).join("|")
    ));
    tableTarget.value = [header, ...bodyRows].join("\n");
    tableTarget.dispatchEvent(new Event("input", { bubbles: true }));
  });

  const imageInput = form.querySelector("[data-image-preview-input]");
  const imagePreview = form.querySelector("[data-image-preview]");
  imageInput?.addEventListener("change", () => {
    const file = imageInput.files?.[0];
    if (!file || !imagePreview) return;
    if (!file.type.startsWith("image/")) {
      imagePreview.innerHTML = "<p class=\"text-muted\">Select an image file to preview it.</p>";
      return;
    }
    const url = URL.createObjectURL(file);
    imagePreview.innerHTML = `<img src="${url}" alt="Selected image preview">`;
  });
});

document.querySelectorAll("[data-sortable-list]").forEach((list) => {
  let dragged = null;
  const status = document.querySelector("[data-sort-status]");
  const saveOrder = async () => {
    const reorderUrl = list.dataset.reorderUrl;
    if (!reorderUrl) return;
    const formData = new FormData();
    list.querySelectorAll("[data-block-id]").forEach((item, index) => {
      formData.append("block_order", item.dataset.blockId);
      const label = item.querySelector("[data-order-label]");
      if (label) label.textContent = String(index + 1);
    });
    const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
    if (csrf) formData.append("csrfmiddlewaretoken", csrf);
    if (status) status.textContent = "Saving order...";
    try {
      const response = await fetch(reorderUrl, { method: "POST", body: formData, headers: { "X-Requested-With": "XMLHttpRequest" } });
      if (!response.ok) throw new Error("Could not save order");
      if (status) status.textContent = "Order saved.";
    } catch (error) {
      if (status) status.textContent = "Order could not be saved. Use Up/Down as fallback.";
    }
  };

  list.addEventListener("dragstart", (event) => {
    dragged = event.target.closest("[data-block-id]");
    if (dragged) dragged.classList.add("is-dragging");
  });
  list.addEventListener("dragend", () => {
    dragged?.classList.remove("is-dragging");
    dragged = null;
    saveOrder();
  });
  list.addEventListener("dragover", (event) => {
    event.preventDefault();
    const target = event.target.closest("[data-block-id]");
    if (!dragged || !target || dragged === target) return;
    const rect = target.getBoundingClientRect();
    const after = event.clientY > rect.top + rect.height / 2;
    target.parentNode.insertBefore(dragged, after ? target.nextSibling : target);
  });
});
