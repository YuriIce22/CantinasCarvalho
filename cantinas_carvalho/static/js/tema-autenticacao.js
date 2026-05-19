const botaoTema = document.getElementById("dark-mode");

document.addEventListener("DOMContentLoaded", () => {

    if (localStorage.getItem("tema") === "dark") {
        document.body.classList.add("tema-escuro");

        if (botaoTema) {
            botaoTema.checked = true;
        }
    }

    const btnTodos = document.querySelector(".btn-categoria");

    if (btnTodos) {
        mostrarCategoria(btnTodos, "todos");
    }
});


if (botaoTema) {
    botaoTema.addEventListener("change", () => {

        document.body.classList.toggle("tema-escuro");

        const darkAtivo =
            document.body.classList.contains("tema-escuro");

        localStorage.setItem(
            "tema",
            darkAtivo ? "dark" : "light"
        );
    });
}

const alertas = document.querySelectorAll('.erro-alerta');
        alertas.forEach(alert => {
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000); // desaparece após 5 segundos
        });

