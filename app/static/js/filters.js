// Aplica los filtros al cambiar el rol o el estado; el texto se envia con Enter o con Buscar
document.querySelectorAll("[data-auto-submit]").forEach((form) => {
  form.addEventListener("change", (event) => {
    if (event.target.matches("select, input[type='radio']")) {
      form.requestSubmit();
    }
  });
});
