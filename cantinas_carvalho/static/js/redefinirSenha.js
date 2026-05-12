// Selecionando os Containers Nomeados como class="container hidden"
const telaEmail = document.querySelector("#redefinir");
const telaCodigo = document.querySelector("#cod");
const telaNovaSenha = document.querySelector("#novaSenha");

// Selecionando os Botões
const btnEnviarEmail = document.querySelector(".botao");
const btnVerificarCodigo = document.querySelector(".botaoCodigo");
const botoesFecharX = document.querySelectorAll(".botao-x");

// 1. Mostrar tela de código e esconder a de email
btnEnviarEmail.addEventListener("click", (e) => {
    e.preventDefault(); // Evita que o <a> recarregue a página
    telaCodigo.classList.remove("hidden");
});

// 2. Mostrar tela de nova senha e esconder a de código
btnVerificarCodigo.addEventListener("click", (e) => {
    e.preventDefault();
    telaCodigo.classList.add("hidden");
    telaNovaSenha.classList.remove("hidden");
});

// 3. Lógica dos botões de fechar (X) - Volta tudo para o início
// Usamos o forEach porque existem vários botões com a classe .botao-x e, para não repetir o código para cada um (como fazer um addEventListener individual para o botaoFechar1, botaoFechar2, etc), aplicamos uma única lógica que funciona para todos os botões de fechar do sistema.
botoesFecharX.forEach(btn => {
    btn.addEventListener("click", (e) => {
        e.preventDefault();
        telaCodigo.classList.add("hidden");
        telaNovaSenha.classList.add("hidden");
        telaEmail.classList.remove("hidden");
    });
});