import os
import random

from flask_bcrypt import generate_password_hash
from flask_mail import Message
from functools import wraps

from flask import render_template, redirect, url_for, session, request, flash
from flask_login import login_user, login_required, current_user
from werkzeug.utils import secure_filename

from cantinas_carvalho import app, bcrypt, db, mail
from cantinas_carvalho.forms import ComumRegisterForm, FuncionarioRegisterForm, LoginForm, ProdutoForm
from cantinas_carvalho.models import Usuario, UsuarioAluno, UsuarioFuncionario, ItemCardapio, Administrador, Categoria, Conta

# =========================
# HOME
# =========================
@app.route("/")
def index():

    # Busca todos os produtos
    produtos = ItemCardapio.query.all()

    return render_template(
        "index.html",
        produtos=produtos
    )

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

        return redirect(url_for('cardapio'))

    return render_template('cadastroAlunos.html', form=register_form)


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

    return render_template('cadastroFuncionario.html', form=register_form)

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
                return redirect(url_for('cardapio'))

            funcionario = UsuarioFuncionario.query.filter_by(id_usuario=usuario.id_usuario).first()
            if funcionario:
                login_user(usuario)
                return redirect(url_for('cardapio'))

            aluno = UsuarioAluno.query.filter_by(id_usuario=usuario.id_usuario).first()
            if aluno:
                login_user(usuario)
                return redirect(url_for('cardapio'))
        else:
            flash('Email ou senha inválidos')

    return render_template('login.html', form=login_form)

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

                email_msg.html = render_template('email.html', codigo=codigo)

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

    return render_template('RedefinirSenha.html', etapa=etapa)

# =========================
# CARDÁPIO
# =========================

@app.route('/cardapio')
def cardapio():
    # Busca todos os itens cadastrados no banco de dados
    itens = ItemCardapio.query.all()
    return render_template('cardapio.html', itens=itens)


# =========================
# TELA ADMIN
# =========================
# @app.route('/admin')
# @login_required
# @admin_required




#=========================
# CADASTRAR PRODUTO
# =========================
@app.route('/admin/cadastrarProduto', methods=['GET', 'POST'])
@login_required
@admin_required
def cadastrarProduto():

    # Pegando as categorias do banco e o formulario de produto
    produtoForm = ProdutoForm()
    categorias = Categoria.query.all()

    produtoForm.categoria.choices = [
        (categoria.id_categoria, categoria.nome)
        for categoria in categorias
    ]

    # Cadastro do produto
    if produtoForm.validate_on_submit():

        # Pegando e salvando imagem
        imagem = produtoForm.imagem.data
        nome_arquivo = secure_filename(imagem.filename)

        caminho_imagem = os.path.join(app.root_path, 'static/img', nome_arquivo)

        imagem.save(caminho_imagem)

        # Cadastrando novo produto
        novo_produto = ItemCardapio(
            nome=produtoForm.nome.data,
            descricao=produtoForm.descricao.data,
            preco=produtoForm.preco.data,
            quantidade_estoque=produtoForm.quantidade_estoque.data,
            categoria_id=produtoForm.categoria.data,
            imagem=nome_arquivo
        )

        db.session.add(novo_produto)
        db.session.commit()

        flash('Produto cadastrado com sucesso.', 'success')

        return redirect(url_for('telaAdmin'))

    return render_template('telaAdmin.html', form=produtoForm)
