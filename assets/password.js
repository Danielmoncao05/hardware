// Mostrar/ocultar senha (change password-visibility). Roda só no navegador: a senha não passa pelo estado do
// Reflex. O botão de olho de cada campo (password_input) traz data-password-toggle com o id do campo.
(function () {
  function setVisible(button, input, visible) {
    input.type = visible ? "text" : "password";
    var label = visible ? "Ocultar senha" : "Mostrar senha";
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("aria-pressed", String(visible));
    button.setAttribute("data-visible", String(visible));
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("[data-password-toggle]");
    if (!button) return;
    var input = document.getElementById(button.getAttribute("data-password-toggle"));
    if (!input) return;
    event.preventDefault();
    setVisible(button, input, input.type === "password");
  });

  // Ao enviar o formulário, todas as senhas dele voltam a ficar ocultas (inclusive se o envio der erro)
  document.addEventListener(
    "submit",
    function (event) {
      var buttons = event.target.querySelectorAll ? event.target.querySelectorAll("[data-password-toggle]") : [];
      buttons.forEach(function (button) {
        var input = document.getElementById(button.getAttribute("data-password-toggle"));
        if (input) setVisible(button, input, false);
      });
    },
    true
  );
})();
