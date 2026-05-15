const botao = document.querySelector("#botao-tema")

if (botao) {
    botao.addEventListener("click", () => {
        body.classList.toggle("tema-escuro");
    });
}