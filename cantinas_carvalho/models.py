import uuid
import pytz
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

db = SQLAlchemy()

# =========================
# SCHEMA: SEGURANCA
# =========================

class Sessao(db.Model):
    __tablename__ = 'sessoes'
    __table_args__ = {'schema': 'seguranca'}

    id_sessao = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'))
    token_hash = db.Column(db.String(255), unique=True, nullable=False)
    ip_origem = db.Column(db.String(45))
    criado_em = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))
    expira_em = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))
    ativo = db.Column(db.Boolean, default=True)


class TentativaLogin(db.Model):
    __tablename__ = 'tentativas_login'
    __table_args__ = {'schema': 'seguranca'}

    id_tentativa = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'))
    ip_origem = db.Column(db.String(45), nullable=False)
    data_hora = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))
    sucesso = db.Column(db.Boolean, nullable=False)


class ResetSenha(db.Model):
    __tablename__ = 'reset_senha'
    __table_args__ = {'schema': 'seguranca'}

    id_reset = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'))
    token_reset = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))
    expira_em = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))
    utilizado = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# =========================
# SCHEMA: USUÁRIO
# =========================

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    __table_args__ = {'schema': 'cantina'}

    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    salt = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    bloqueado = db.Column(db.Boolean, default=False)
    tentativas_falhas = db.Column(db.Integer, default=0)
    ultimo_login = db.Column(db.DateTime)
    criado_em = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))

    def get_id(self):
        return str(self.id_usuario)


    @validates('email')
    def validar_email(self, key, value):
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", value):
            raise ValueError("Formato de e-mail inválido.")
        return value

    @validates('tentativas_falhas')
    def validar_tentativas(self, key, value):
        if value < 0:
            raise ValueError("Tentativas falhas não podem ser negativas.")
        return value


class UsuarioAluno(db.Model):
    __tablename__ = 'usuario_aluno'
    __table_args__ = {'schema': 'cantina'}

    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'), primary_key=True)


class UsuarioFuncionario(db.Model):
    __tablename__ = 'usuario_funcionario'
    __table_args__ = {'schema': 'cantina'}

    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'), primary_key=True)
    id_conta = db.Column(db.Integer, db.ForeignKey('cantina.conta.id_conta'), unique=True)
    nif = db.Column(db.String(7), unique=True, nullable=False)

    @validates('nif')
    def validar_nif(self, key, value):
        if not re.match(r"^[0-9]{7}$", value):
            raise ValueError("NIF deve ter 7 dígitos.")
        return value


class Administrador(db.Model):
    __tablename__ = 'administrador'
    __table_args__ = {'schema': 'cantina'}

    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'), primary_key=True)
    nivel_acesso = db.Column(db.String(50), default='admin')

    @validates('nivel_acesso')
    def validar_nivel(self, key, value):
        if value not in ['admin', 'superadmin']:
            raise ValueError("Nível inválido.")
        return value

# =========================
# CONTA
# =========================

class Conta(db.Model):
    __tablename__ = 'conta'
    __table_args__ = {'schema': 'cantina'}

    id_conta = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'), unique=True)
    saldo = db.Column(db.Numeric(7, 2), default=Decimal("0.00"), nullable=False)
    status = db.Column(db.String(20), default='ativo')
    data_criacao = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))

    @validates('saldo')
    def validar_saldo(self, key, value):
        if value < 0:
            raise ValueError("Saldo não pode ser negativo.")
        return value

    @validates('status')
    def validar_status(self, key, value):
        if value not in ['ativo', 'inativo']:
            raise ValueError("Status inválido.")
        return value

# =========================
# CARDÁPIO
# =========================

class Categoria(db.Model):
    __tablename__ = 'categoria'
    __table_args__ = {'schema': 'cantina'}

    id_categoria = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300), nullable=False)


class ItemCardapio(db.Model):
    __tablename__ = 'item_cardapio'
    __table_args__ = {'schema': 'cantina'}

    id_item_cardapio = db.Column(db.Integer, primary_key=True)
    id_categoria = db.Column(db.Integer, db.ForeignKey('cantina.categoria.id_categoria'))
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300))
    preco = db.Column(db.Numeric(5, 2), nullable=False)
    disponivel = db.Column(db.Boolean, default=True)
    quantidade_estoque = db.Column(db.Integer, default=0)
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    imagem = db.Column(db.String(255))

    @validates('preco')
    def validar_preco(self, key, value):
        if value <= 0:
            raise ValueError("Preço inválido.")
        return value

    @validates('quantidade_estoque')
    def validar_estoque(self, key, value):
        if value < 0:
            raise ValueError("Estoque inválido.")
        return value

class ItemVenda(db.Model):
    __tablename__ = "item_venda"
    __table_args__ = {"schema": "cantina"}

    id_item_venda = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('cantina.pedido.id_pedido'))
    id_item_cardapio = db.Column(db.Integer, db.ForeignKey('cantina.item_cardapio.id_item_cardapio'))
    quantidade = db.Column(db.Integer)
    valor_unitario = db.Column(db.Numeric(5, 2), nullable=False)

    @validates('valor_unitario')
    def validar_valor_unitario(self, key, value):
        if value < 0:
            raise ValueError("Valor inválido.")
        return value

# =========================
# PEDIDO
# =========================

class Pedido(db.Model):
    __tablename__ = 'pedido'
    __table_args__ = {'schema': 'cantina'}

    id_pedido = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('cantina.usuario.id_usuario'))
    status = db.Column(db.String(20), default='pendente')
    valor_pedido = db.Column(db.Numeric(7, 2), nullable=False)
    qr_code_retirada = db.Column(db.String(100), nullable=False)
    codigo_unico = db.Column(db.String(100), nullable=False)
    data_hora = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc))

    @validates('valor_pedido')
    def validar_valor(self, key, value):
        if value < 0:
            raise ValueError("Valor inválido.")
        return value

# =========================
# PAGAMENTO
# =========================

class Pagamento(db.Model):
    __tablename__ = 'pagamento'
    __table_args__ = {'schema': 'cantina'}

    id_pagamento = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('cantina.pedido.id_pedido'))
    id_conta = db.Column(db.Integer, db.ForeignKey('cantina.conta.id_conta'))
    valor_pagamento = db.Column(db.Numeric(7, 2), nullable=False)
    status = db.Column(db.String(20), default='pendente')

    @validates('valor_pagamento')
    def validar_valor(self, key, value):
        if value <= 0:
            raise ValueError("Pagamento inválido.")
        return value