// Cambia entre las pestañas de Iniciar sesión y Registro sin recargar la página
document.querySelectorAll("[data-pestanas]").forEach((lista) => {
  const pestanas = [...lista.querySelectorAll('[role="tab"]')];

  const activar = (elegida) => {
    pestanas.forEach((pestana) => {
      const activa = pestana === elegida;
      pestana.setAttribute("aria-selected", String(activa));
      pestana.tabIndex = activa ? 0 : -1;
      document.getElementById(pestana.getAttribute("aria-controls")).hidden = !activa;
    });
    lista.dataset.activo = elegida.dataset.pestana;
    history.replaceState(null, "", elegida.href);
  };

  pestanas.forEach((pestana, indice) => {
    pestana.addEventListener("click", (evento) => {
      evento.preventDefault();
      activar(pestana);
    });

    pestana.addEventListener("keydown", (evento) => {
      if (evento.key !== "ArrowLeft" && evento.key !== "ArrowRight") return;
      const paso = evento.key === "ArrowRight" ? 1 : -1;
      const siguiente = pestanas[(indice + paso + pestanas.length) % pestanas.length];
      siguiente.focus();
      activar(siguiente);
    });
  });
});
