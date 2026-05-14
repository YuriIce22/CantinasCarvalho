import os
import random
from flask_mail import Message
from functools import wraps

from flask import render_template, redirect, url_for, session, request, flash
from flask_login import login_user, login_required, current_user
from werkzeug.utils import secure_filename

from cantinas_carvalho import app, bcrypt, db, mail
from cantinas_carvalho.forms import ComumRegisterForm, FuncionarioRegisterForm, LoginForm, ProdutoForm
from cantinas_carvalho.models import Usuario, UsuarioAluno, UsuarioFuncionario, ItemCardapio, Administrador, Categoria

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

        funcionario = UsuarioFuncionario(
            id_usuario=novo_usuario.id_usuario,
            nif=register_form.nif.data
        )

        db.session.add(funcionario)
        db.session.commit()

        return redirect(url_for('cardapio'))

    return render_template('cadastroFuncionario.html', form=register_form)


# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=login_form.email.data).first()

        # Aqui a gente checa se o usuário existe e se a senha está certa
        if usuario and bcrypt.check_password_hash(usuario.senha_hash, login_form.senha.data):
            login_user(usuario)  # ESTA LINHA É A CHAVE! Ela "loga" o usuário.
            return redirect(url_for('cardapio'))

    return render_template('login.html', form=login_form)

# =========================
# REDEFINIR SENHA
# =========================

@app.route('/esqueceuSenha', methods=['GET', 'POST'])
def esqueceuSenha():

    etapa = session.get('etapa', 'email')

    # ======================
    # ETAPA EMAIL
    # ======================

    if request.method == 'POST':

        # ENVIAR EMAIL

        if 'enviar_email' in request.form:

            email = request.form.get('email')

            usuario = Usuario.query.filter_by(email=email).first()

            if usuario:

                codigo = str(random.randint(1000, 9999))

                session['codigo'] = codigo
                session['usuario_id'] = usuario.id_usuario
                session['etapa'] = 'codigo'

                email_msg = Message(

                    subject='Recuperação de Senha',

                    sender=app.config['MAIL_USERNAME'],

                    recipients=[email]
                )

                email_msg.body = f'''
                    Seu código é:

                    {codigo}
                '''

                mail.send(email_msg)

                etapa = 'codigo'

            else:

                flash('E-mail não encontrado!')

        # ======================
        # VALIDAR CODIGO
        # ======================

        elif 'verificar_codigo' in request.form:

            codigo_digitado = request.form.get('codigo')

            if codigo_digitado == session.get('codigo'):

                session['etapa'] = 'nova_senha'

                etapa = 'nova_senha'

            else:

                flash('Código inválido!')

                etapa = 'codigo'

        # ======================
        # NOVA SENHA
        # ======================

        elif 'alterar_senha' in request.form:

            senha = request.form.get('senha')

            confirmar = request.form.get('confirmar')

            if senha != confirmar:

                flash('As senhas não coincidem!')

                etapa = 'nova_senha'

            else:

                usuario = Usuario.query.get(
                    session.get('usuario_id')
                )

                usuario.senha_hash = generate_password_hash(senha)

                db.session.commit()

                session.clear()

                flash('Senha alterada com sucesso!')

                return redirect(url_for('login'))

    return render_template(
        'RedefinirSenha.html',
        etapa=etapa
    )
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
