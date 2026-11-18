// Cambia entre las pestanas de Iniciar sesion y Registro sin recargar la pagina
document.querySelectorAll("[data-pestanas]").forEach((tabList) => {
  const tabs = [...tabList.querySelectorAll('[role="tab"]')];

  const activate = (selected) => {
    tabs.forEach((tab) => {
      const isActive = tab === selected;
      tab.setAttribute("aria-selected", String(isActive));
      tab.tabIndex = isActive ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !isActive;
    });
    tabList.dataset.activo = selected.dataset.pestana;
    history.replaceState(null, "", selected.href);
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", (event) => {
      event.preventDefault();
      activate(tab);
    });

    tab.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      const step = event.key === "ArrowRight" ? 1 : -1;
      const next = tabs[(index + step + tabs.length) % tabs.length];
      next.focus();
      activate(next);
    });
  });
});
