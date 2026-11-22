// Las notificaciones se cierran solas; con el mouse encima se quedan hasta que se retire
document.querySelectorAll(".toast").forEach((toast) => {
  const close = () => {
    toast.classList.add("toast-saliendo");
    setTimeout(() => toast.remove(), 200);
  };
  let timer = setTimeout(close, 8000);

  toast.querySelector("[data-cerrar]").addEventListener("click", close);
  toast.addEventListener("mouseenter", () => clearTimeout(timer));
  toast.addEventListener("mouseleave", () => {
    timer = setTimeout(close, 3000);
  });
});
