const botao = document.querySelector("#botao-tema")
const body = document.querySelector("body")

botao.addEventListener("click", () => {
    body.classList.toggle("tema-escuro");
});