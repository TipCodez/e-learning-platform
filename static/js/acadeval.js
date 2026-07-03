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
