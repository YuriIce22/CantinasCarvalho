import os
import random

from flask_bcrypt import generate_password_hash
from flask_mail import Message
from functools import wraps

from flask import render_template, redirect, url_for, session, request, flash, jsonify
from flask_login import login_user, login_required, current_user
from werkzeug.utils import secure_filename

from cantinas_carvalho import app, bcrypt, db, mail
from cantinas_carvalho.forms import ComumRegisterForm, FuncionarioRegisterForm, LoginForm, ProdutoForm
from cantinas_carvalho.models import Usuario, UsuarioAluno, UsuarioFuncionario, ItemCardapio, Administrador, Categoria, Conta, ItemVenda, Pedido

carrinho = []

# =========================
# HOME
# =========================

@app.route("/")
def index():

    # Busca todos os produtos
    produtos = ItemCardapio.query.all()

    return render_template("index.html",produtos=produtos)

# Criação do @admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            return redirect(url_for('login'))

        admin = Administrador.query.filter_by(
            id_usuario=current_user.id_usuario
        ).first()

        if not admin:
            flash('Acesso permitido apenas para administradores.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function

# =========================
# CADASTRO ALUNO
# =========================

@app.route('/cadastarAlunos', methods=['GET', 'POST'])
def cadastrarAluno():
    register_form = ComumRegisterForm()

    if register_form.validate_on_submit():
        senha_hash = bcrypt.generate_password_hash(
            register_form.senha.data
        ).decode('utf-8')

        novo_usuario = Usuario(
            nome=register_form.nome.data,
            email=register_form.email.data,
            senha_hash=senha_hash,
            telefone=register_form.telefone.data,
            salt = os.urandom(16).hex()
        )

        db.session.add(novo_usuario)
        db.session.commit()

        aluno = UsuarioAluno(id_usuario=novo_usuario.id_usuario)
        db.session.add(aluno)
        db.session.commit()

        return redirect(url_for('listarCardapio'))

    return render_template('cadastro/cadastroAlunos.html', form=register_form)

# =========================
# CADASTRO FUNCIONARIO
# =========================

@app.route('/cadastrarFuncionario', methods=['GET', 'POST'])
def cadastrarFuncionario():
    register_form = FuncionarioRegisterForm()

    if register_form.validate_on_submit():
        # 1. Criptografa a senha vinda do input HTML (name="senha")
        senha_criptografada = bcrypt.generate_password_hash(
            register_form.senha.data
        ).decode('utf-8')

        # 2. Cria o Usuário base batendo exatamente com as colunas da sua tabela
        novo_usuario = Usuario(
            nome=register_form.nome.data,
            email=register_form.email.data,
            senha_hash=senha_criptografada,  # Alinhado com o banco físico!
            telefone=register_form.telefone.data,
            salt=os.urandom(16).hex()
        )
        db.session.add(novo_usuario)
        db.session.commit()  # Banco gera o id_usuario

        # 3. Cria a Conta de forma automatizada
        nova_conta = Conta(
            id_usuario=novo_usuario.id_usuario,
            saldo=0.00
            # se no seu modelo aceitar o campo status, deixe: status='ativo'
        )
        db.session.add(nova_conta)
        db.session.commit()

        # 4. Cria o vínculo do Funcionário
        funcionario = UsuarioFuncionario(
            id_usuario=novo_usuario.id_usuario,
            id_conta=nova_conta.id_conta,
            nif=register_form.nif.data
        )
        db.session.add(funcionario)
        db.session.commit()

        return redirect(url_for('cardapio'))

    else:
        # ATENÇÃO: Verifique o que vai printar aqui no console se a página limpar!
        print("ERROS DO FORM ATUALIZADO:", register_form.errors)

    return render_template('cadastro/cadastroFuncionario.html', form=register_form)

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=login_form.email.data).first()

        if usuario and bcrypt.check_password_hash(usuario.senha_hash, login_form.senha.data):

            admin = Administrador.query.filter_by(id_usuario=usuario.id_usuario).first()
            if admin:
                login_user(usuario)
                definir_perfil(usuario)
                return redirect(url_for('telaAdmin'))

            funcionario = UsuarioFuncionario.query.filter_by(id_usuario=usuario.id_usuario).first()
            if funcionario:
                login_user(usuario)
                definir_perfil(usuario)
                return redirect(url_for('cardapioFuncionario'))

            aluno = UsuarioAluno.query.filter_by(id_usuario=usuario.id_usuario).first()
            if aluno:
                login_user(usuario)
                definir_perfil(usuario)
                return redirect(url_for('listarCardapio'))
        else:
            flash('Email ou senha inválidos')

    return render_template('login/login.html', form=login_form)

def definir_perfil(usuario):
    if Administrador.query.filter_by(id_usuario=usuario.id_usuario).first():
        session['perfil'] = 'admin'

    elif UsuarioFuncionario.query.filter_by(id_usuario=usuario.id_usuario).first():
        session['perfil'] = 'funcionario'

    elif UsuarioAluno.query.filter_by(id_usuario=usuario.id_usuario).first():
        session['perfil'] = 'aluno'

    else:
        session['perfil'] = 'desconhecido'

# =========================
# REDEFINIR SENHA
# =========================

@app.route('/esqueceuSenha', methods=['GET', 'POST'])
def esqueceuSenha():

    if request.method == 'POST':

        # ======================
        # ENVIAR EMAIL
        # ======================
        if request.form.get('enviar_email'):

            email = request.form.get('email')
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario:

                codigo = str(random.randint(1000, 9999))

                session['codigo'] = codigo
                session['usuario_id'] = usuario.id_usuario
                session['etapa'] = 'codigo'

                email_msg = Message(
                    subject='🔒 Recuperação de Senha - Cantinas Carvalho',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )

                email_msg.html = render_template('login/email.html', codigo=codigo)

                mail.send(email_msg)

                return redirect(url_for('esqueceuSenha'))

            else:

                flash('E-mail não encontrado!')
                return redirect(url_for('esqueceuSenha'))

        # ======================
        # VALIDAR CÓDIGO
        # ======================
        elif request.form.get('verificar_codigo'):

            codigo_digitado = (
                request.form.get('c1', '') +
                request.form.get('c2', '') +
                request.form.get('c3', '') +
                request.form.get('c4', '')
            )

            if codigo_digitado == session.get('codigo'):

                session['etapa'] = 'nova_senha'
                return redirect(url_for('esqueceuSenha'))

            else:

                flash('Código inválido!')
                return redirect(url_for('esqueceuSenha'))

        # ======================
        # ALTERAR SENHA
        # ======================
        elif request.form.get('alterar_senha'):

            senha = request.form.get('senha')
            confirmar = request.form.get('confirmar')

            if senha != confirmar:

                flash('As senhas não coincidem!')
                return redirect(url_for('esqueceuSenha'))

            usuario = Usuario.query.get(session.get('usuario_id'))

            if usuario:

                usuario.senha_hash = generate_password_hash(senha).decode('utf-8')
                db.session.commit()

                session.clear()

                flash('Senha alterada com sucesso!')
                return redirect('/login')

            else:

                flash('Usuário não encontrado!')
                return redirect(url_for('login'))

    # ======================
    # GET (ÚNICA FONTE DA ETAPA)
    # ======================
    etapa = session.get('etapa', 'email')

    return render_template('login/RedefinirSenha.html', etapa=etapa)

# =========================
# CARDÁPIO
# =========================

@app.route("/categorias", methods=["GET"])
def listarCategorias():
    categorias_banco = Categoria.query.all()

    categorias = []

    for categoria in categorias_banco:
        categorias.append({
            "id": categoria.id_categoria,
            "nome": categoria.nome
        })

    return render_template('cardapio.html')

@app.route("/cardapio", methods=["GET"])
def listarCardapio():
    id_categoria = request.args.get('categoria')

    categorias = Categoria.query.all()

    if id_categoria:
        produtos = ItemCardapio.query.filter_by(id_categoria=id_categoria, disponivel=True).all()

    else:
        produtos = ItemCardapio.query.filter_by(disponivel=True).all()

    return render_template('cardapio/cardapio.html', categorias=categorias, produtos=produtos)

# Rota de carrinho
@app.route("/carrinho", methods=["POST"])
def adicionarCarrinho():

    dados = request.get_json()

    id_produto = dados["produto_id"]
    quantidade = dados["quantidade"]

    produto = ItemCardapio.query.get(id_produto)

    if not produto:

        return jsonify({
            "mensagem": "produto não encontrado!",
        }), 404

    item = {
        "id": produto.id_item_cardapio,
        "nome": produto.nome,
        "preco": float(produto.preco),
        "imagem": produto.imagem,
        "quantidade": quantidade
    }

    carrinho.append(item)

    return jsonify({
        "status": "sucesso",
        "produto_nome": produto.nome
    })

@app.route("/carrinho", methods=["GET"])
def listarCarrinho():

    valor_total = 0

    for item in carrinho:
        subtotal = item["preco"] * item["quantidade"]
        valor_total += subtotal

    return render_template('carrinho.html', valor_total=valor_total)

@app.route("/carrinho/<int:id_produto>", methods=["DELETE"])
def removerCarrinho(id_produto):

    for item in carrinho:

        if item["id"] == id_produto:

            carrinho.remove(item)

            return jsonify({
                "mensagem": "item removido"
            })

    return jsonify({
        "erro": "item não encontrado"
    }), 404

# Rota de pedido
@app.route("/pedido", methods=["POST"])
def criarPedido():
    dados = request.get_json()

    id_usuario = dados["id_usuario"]

    valor_total = 0

    for item in carrinho:
        valor_total += (item["preco"] * item["quantidade"])

    pedido = Pedido(id_usuario = id_usuario, valor_pedido = valor_total, qr_code_retirada="qr_teste", codigo_unico = "codigo_teste")

    db.session.add(pedido)
    db.session.commit()

    for item in carrinho:
        item_venda = ItemVenda(id_pedido = pedido.id_pedido, id_item_cardapio = item["id"], quantidade = item["quantidade"], valor_unitario = item["preco"])

        db.session.add(item_venda)

    db.session.commit()

    carrinho.clear()

    return jsonify({
        "mensagem": "pedido criado com sucesso",
        "id_pedido": pedido.id_pedido
    })

@app.route("/cardapioFuncionario")
@login_required
def cardapioFuncionario():

    categorias = Categoria.query.all()

    produtos = ItemCardapio.query.filter_by(disponivel=True).all()

    return render_template("cardapio/cardapioFuncionario.html", categorias=categorias, produtos=produtos)

@app.route("/perfil")
@login_required
def perfilFuncionario():

    funcionario = UsuarioFuncionario.query.filter_by(id_usuario=current_user.id_usuario).first()

    if not funcionario:
        return redirect(url_for("listarCardapio"))

    return render_template("conta.html")

# =========================
# TELA ADMIN
# =========================

@app.route('/admin')
@login_required
@admin_required
def telaAdmin():

    produtos = ItemCardapio.query.order_by(ItemCardapio.id_item_cardapio.desc()).all()

    total_produtos = ItemCardapio.query.count()

    produtos_disponiveis = ItemCardapio.query.filter_by(disponivel=True).count()

    produtos_indisponiveis = ItemCardapio.query.filter_by(disponivel=False).count()

    return render_template(
        'admin/produtos.html',
        produtos=produtos,
        total_produtos=total_produtos,
        produtos_disponiveis=produtos_disponiveis,
        produtos_indisponiveis=produtos_indisponiveis,
        admin_nome=current_user.nome
    )

@app.route('/admin/cadastrarProduto', methods=['GET', 'POST'])
@login_required
@admin_required
def cadastrarProduto():

    produtoForm = ProdutoForm()
    categorias = Categoria.query.all()
    produtoForm.categoria.choices = [(categoria.id_categoria, categoria.nome) for categoria in categorias]

    if produtoForm.validate_on_submit():
        nome_arquivo = None

        if produtoForm.imagem.data:

            imagem = produtoForm.imagem.data

            # EXTENSÃO DA IMAGEM
            extensao = os.path.splitext(secure_filename(imagem.filename))[1]

            # NOME BASE VINDO DO CAMPO "nome"
            nome_base = secure_filename(produtoForm.nome.data.lower().replace(' ', '_'))

            pasta_upload = os.path.join(app.root_path,'static/img/produtosImg')

            os.makedirs(pasta_upload, exist_ok=True)

            # NOME INICIAL
            nome_arquivo = f'{nome_base}{extensao}'
            caminho_imagem = os.path.join(pasta_upload, nome_arquivo)
            contador = 1

            # VERIFICA SE JÁ EXISTE
            while os.path.exists(caminho_imagem):

                nome_arquivo = f'{nome_base}_{contador}{extensao}'
                caminho_imagem = os.path.join(pasta_upload, nome_arquivo)
                contador += 1

            imagem.save(caminho_imagem)

        novo_produto = ItemCardapio(
            nome=produtoForm.nome.data,
            descricao=produtoForm.descricao.data,
            preco=produtoForm.preco.data,
            quantidade_estoque=produtoForm.quantidade_estoque.data,
            id_categoria=produtoForm.categoria.data,
            imagem=nome_arquivo,
            disponivel=True
        )

        db.session.add(novo_produto)
        db.session.commit()

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('telaAdmin'))

    return render_template('admin/cadastrarProduto.html', form=produtoForm)

# =========================
# PEDIDOS ADMIN
# =========================

@app.route('/admin/pedidos')
@login_required
@admin_required
def pedidoAdmin():

    pedidos = Pedido.query.order_by(Pedido.id_pedido.desc()).all()

    total_pedidos = Pedido.query.count()

    pedidos_pendentes = Pedido.query.filter_by(status='pendente').count()

    pedidos_entregues = Pedido.query.filter_by(status='entregue').count()

    pedidos_cancelados = Pedido.query.filter_by(status='cancelado').count()

    return render_template(
        'admin/pedidos.html',

        pedidos=pedidos,
        total_pedidos=total_pedidos,
        pedidos_pendentes=pedidos_pendentes,
        pedidos_entregues=pedidos_entregues,
        pedidos_cancelados=pedidos_cancelados,
        admin_nome=current_user.nome
    )

# =========================
# ALTERAR STATUS PEDIDO
# =========================

@app.route('/admin/pedido/<int:id_pedido>/status/<string:novo_status>')
@login_required
@admin_required
def alterarStatusPedido(id_pedido, novo_status):

    pedido = Pedido.query.get_or_404(id_pedido)

    pedido.status = novo_status

    db.session.commit()

    flash('Status do pedido atualizado!', 'success')

    return redirect(url_for('pedidoAdmin'))

# =========================
# RELATÓRIOS ADMIN
# =========================

@app.route('/admin/relatorios')
@login_required
@admin_required
def relatorioAdmin():

    faturamento_total = db.session.query(func.sum(Pedido.valor_pedido)).filter(Pedido.status == 'entregue').scalar() or 0

    total_pedidos = Pedido.query.count()

    total_produtos = ItemCardapio.query.count()

    total_usuarios = Usuario.query.count()

    pedidos_entregues = Pedido.query.filter_by(status='entregue').count()

    pedidos_pendentes = Pedido.query.filter_by(status='pendente').count()

    return render_template(
        'admin/relatorios.html',

        faturamento_total=faturamento_total,
        total_pedidos=total_pedidos,
        total_produtos=total_produtos,
        total_usuarios=total_usuarios,
        pedidos_entregues=pedidos_entregues,
        pedidos_pendentes=pedidos_pendentes,
        admin_nome=current_user.nome
    )

# =========================
# USUÁRIOS ADMIN
# =========================

@app.route('/admin/usuarios')
@login_required
@admin_required
def usuarioAdmin():

    usuarios = Usuario.query.order_by(Usuario.id_usuario.desc()).all()

    total_usuarios = Usuario.query.count()
    total_alunos = UsuarioAluno.query.count()
    total_funcionarios = UsuarioFuncionario.query.count()
    total_admins = Administrador.query.count()

    return render_template(
        'admin/usuarios.html',

        usuarios=usuarios,
        total_usuarios=total_usuarios,
        total_alunos=total_alunos,
        total_funcionarios=total_funcionarios,
        total_admins=total_admins,
        admin_nome=current_user.nome
    )