# import nome
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from sqlalchemy.sql.functions import user
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import DecimalField, IntegerField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from cantinas_carvalho.models import *


class ComumRegisterForm(FlaskForm):
    nome = StringField('Nome do Usuário', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=8, max=20)])
    confirm_senha = PasswordField('', validators=[DataRequired(), EqualTo('senha')])
    telefone = StringField('Telefone', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')


    def validate_telefone(self, telefone):
        telefone = Usuario.query.filter_by(telefone=telefone.data).first()
        if telefone:
            raise ValidationError("Telefone já cadastrado. Por favor, escolha outro telefone.")
        return None

    def validate_email(self, email):
        User = Usuario.query.filter_by(email=email.data).first()
        if User:
            raise ValidationError("E-mail já cadastrado. Por favor, escolha outro email.")
        return None


class FuncionarioRegisterForm(FlaskForm):
    nome = StringField('Nome do Usuário', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=8, max=20)])
    confirm_senha = PasswordField('', validators=[DataRequired(), EqualTo('senha')])
    telefone = StringField('Telefone', validators=[DataRequired()])
    nif = StringField('NIF', validators=[DataRequired(), Length(min=7, max=7)])
    submit = SubmitField('Cadastrar')

    def validate_telefone(self, telefone):
        existing = Usuario.query.filter_by(telefone=telefone.data).first()
        if existing:
            raise ValidationError("Telefone já cadastrado.")

    def validate_email(self, email):
        existing = Usuario.query.filter_by(email=email.data).first()
        if existing:
            raise ValidationError("E-mail já cadastrado.")

    def validate_nif(self, nif):
        nif = UsuarioFuncionario.query.filter_by(nif=nif.data).first()
        if nif:
            raise ValidationError("NIF já cadastrado!")


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

    def validate_email(self, email):
        existing = Usuario.query.filter_by(email=email.data).first()
        if existing:
            raise ValidationError("E-mail já cadastrado.")


class ProdutoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired(), Length(min=2, max=300)])
    preco = DecimalField('Preço', validators=[DataRequired(), NumberRange(min=0, max=9999.99)], places=2)
    quantidade_estoque = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=0)])
    categoria = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    imagem = FileField('Imagem', validators=[FileRequired(), FileAllowed(["jpg", "jpeg", "png", "webp"],
                                                                                "Apenas Imagens!")])
    submit = SubmitField('CadastrarProduto')

    def validate_nome(self, nome):
        nome = ItemCardapio.query.filter_by(nome=nome.data).first()
        if nome:
            raise ValidationError("Produto já cadastrado.")
        return None

    def validate_preco(self, preco):
        if preco.data <= 0:
            raise ValidationError("O preço não pode ser menor que zero.")
        return None