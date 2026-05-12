/* conteúdo de alternação de Modo Claro / Modo Escuro das tela de Login e Cadastros*/

const botao = document.querySelector("#botao-tema")
const body = document.querySelector("body")

botao.addEventListener("click", () => {
    body.classList.toggle("tema-escuro");
});