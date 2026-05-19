// TEMA
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

// BOTÃO ALMOÇO
function irParaAlmoco() {
    const btnTodos = document.querySelector(".btn-categoria");
    if (btnTodos) {
        mostrarCategoria(btnTodos, "todos");
    }

    setTimeout(() => {
        const secaoAlmoco = document.getElementById('secao-almoco');
        if (secaoAlmoco) {
            secaoAlmoco.scrollIntoView({ behavior: 'smooth' });
        }
    }, 50);
}

// BOTÃO CONTA
function irParaConta() {
    window.location.href = "/perfil";
}

// FILTRO DE CATEGORIAS
function mostrarCategoria(botao, categoriaId) {
    const botoes = document.querySelectorAll(".btn-categoria");
    const secoes = document.querySelectorAll(".secao-produtos");

    botoes.forEach(btn => btn.classList.remove("active"));
    botao.classList.add("active");

    secoes.forEach(secao => {
        const idSecao = secao.id.replace("secao-", "");
        if (categoriaId === "todos" || idSecao == categoriaId) {
            secao.style.display = "block";
        } else {
            secao.style.display = "none";
        }
    });
}

window.mostrarCategoria = mostrarCategoria;

// NOTIFICAÇÃO
async function adicionarCarrinho(produtoId) {
    try {
        const resposta = await fetch("/carrinho", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                produto_id: produtoId,
                quantidade: 1
            })
        });

        if (resposta.ok) {
            const dados = await resposta.json();

            const badge = document.querySelector(".badge");
            let valorAtual = parseInt(badge.textContent || "0");
            badge.textContent = valorAtual + 1;

            if (dados.status === "sucesso") {
                const toast = document.getElementById("toast-notification");
                const toastMessage = document.getElementById("toast-message");

                toastMessage.innerHTML = `O pedido: <strong>${dados.produto_nome}</strong> foi adicionado ao carrinho com sucesso!`;

                toast.classList.add("toast-show");

                setTimeout(() => {
                    toast.classList.remove("toast-show");
                }, 3500);
            }
        } else {
            console.error("Erro ao adicionar item ao carrinho no servidor.");
        }
    } catch (erro) {
        console.error("Erro na requisição do carrinho:", erro);
    }
}

// BOTÃO SUBIR
const btnSubir = document.getElementById("btnSubir");

window.onscroll = function () {
    if (!btnSubir) return;

    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        btnSubir.style.display = "flex";
    }
    else {
        btnSubir.style.display = "none";
    }

};

function subirTopo() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

window.subirTopo = subirTopo;


