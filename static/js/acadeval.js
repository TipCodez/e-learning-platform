document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".toast-stack .alert");
  alerts.forEach((alert) => {
    window.setTimeout(() => {
      alert.classList.remove("show");
    }, 5000);
  });
});
