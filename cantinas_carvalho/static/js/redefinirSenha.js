// TELAS

const telaEmail = document.querySelector("#redefinir");
const telaCodigo = document.querySelector("#cod");
const telaNovaSenha = document.querySelector("#novaSenha");


const formEmail = document.querySelector("#formEmail");
const formCodigo = document.querySelector("#formCodigo");
const formSenha = document.querySelector("#formSenha");

// BOTÕES X

const botoesFecharX = document.querySelectorAll(".botao-x");

// ==========================
// ENVIAR EMAIL
// ==========================

formEmail.addEventListener("submit", async (e) => {

    e.preventDefault();

    const email = document.querySelector("#email").value;

    const resposta = await fetch("/esqueceuSenha", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            email: email
        })

    });

    const dados = await resposta.json();

    if (dados.status === "ok") {

        telaEmail.classList.add("hidden");

        telaCodigo.classList.remove("hidden");

    } else {

        alert(dados.mensagem);

    }

});

// ==========================
// VERIFICAR CODIGO
// ==========================

formCodigo.addEventListener("submit", async (e) => {

    e.preventDefault();

    const codigo = document.querySelector("#codigo").value;

    const resposta = await fetch("/verificarCodigo", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            codigo: codigo
        })

    });

    const dados = await resposta.json();

    if (dados.status === "ok") {

        telaCodigo.classList.add("hidden");

        telaNovaSenha.classList.remove("hidden");

    } else {

        alert(dados.mensagem);

    }

});

// ==========================
// ALTERAR SENHA
// ==========================

formSenha.addEventListener("submit", async (e) => {

    e.preventDefault();

    const senha = document.querySelector("#senha").value;

    const confirmarSenha = document.querySelector("#confirmarSenha").value;

    const resposta = await fetch("/novaSenha", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            senha: senha,

            confirmarSenha: confirmarSenha

        })

    });

    const dados = await resposta.json();

    if (dados.status === "ok") {

        alert("Senha alterada com sucesso!");

        window.location.href = "/login";

    } else {

        alert(dados.mensagem);

    }

});

// ==========================
// FECHAR
// ==========================

botoesFecharX.forEach(btn => {

    btn.addEventListener("click", (e) => {

        e.preventDefault();

        telaCodigo.classList.add("hidden");

        telaNovaSenha.classList.add("hidden");

        telaEmail.classList.remove("hidden");

    });

});