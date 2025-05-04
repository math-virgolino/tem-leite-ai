from app.extensions import db, login_manager  # Importe do arquivo extensions.py
from flask_login import UserMixin
from app.extensions import db


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'  # Nome da tabela no banco de dados
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'doador' ou 'receptor'
    endereco = db.Column(db.String(200), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    cep = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.tipo}')"
    
class Doacao(db.Model):
    __tablename__ = 'doacao'  # Nome da tabela no banco de dados
    id = db.Column(db.Integer, primary_key=True)
    doador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Chave estrangeira para o doador
    data_doacao = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Data da doação
    quantidade = db.Column(db.Float, nullable=False)  # Quantidade de leite doada (em litros, por exemplo)

    # Relacionamento com o doador
    doador = db.relationship('User', backref=db.backref('doacoes', lazy=True))

    def __repr__(self):
        return f"Doacao('{self.doador.username}', '{self.data_doacao}', '{self.quantidade}')"
    
class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    remetente = db.relationship('User', foreign_keys=[remetente_id], backref='mensagens_enviadas')
    destinatario = db.relationship('User', foreign_keys=[destinatario_id], backref='mensagens_recebidas')

    def __repr__(self):
        return f"Mensagem('{self.remetente.username}', '{self.destinatario.username}', '{self.timestamp}')"
