from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Doacao
from math import radians, sin, cos, sqrt, atan2
import requests
from datetime import datetime

def init_routes(app):
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            print(f"Tentativa de login: email={email}, password={password}")  # Depuração

            user = User.query.filter_by(email=email).first()
            if user:
                print(f"Usuário encontrado: {user.email}, tipo={user.tipo}")  # Depuração
                if user.password == password:
                    login_user(user)
                    print("Login bem-sucedido!")  # Depuração
                    if user.tipo == 'doador':
                        return redirect(url_for('dashboard_doador'))
                    else:
                        return redirect(url_for('dashboard_receptor'))
                else:
                    print("Senha incorreta!")  # Depuração
                    flash('Senha incorreta.', 'danger')
            else:
                print("Usuário não encontrado!")  # Depuração
                flash('E-mail não encontrado.', 'danger')

        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    def obter_coordenadas(endereco):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': endereco,
            'format': 'json'
        }
        headers = {
            'User-Agent': 'TemLeiteAi/1.0'  # Adicione um User-Agent para evitar bloqueios
        }
        response = requests.get(url, params=params, headers=headers).json()
        if response:
            latitude = float(response[0]['lat'])
            longitude = float(response[0]['lon'])
            return latitude, longitude
        return None, None

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            tipo = request.form.get('tipo')  # 'doador' ou 'receptor'
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            cep = request.form.get('cep')

            # Obter latitude e longitude a partir do endereço
            latitude, longitude = obter_coordenadas(f"{endereco}, {cidade}, {estado}, {cep}")
            if latitude is None or longitude is None:
                flash('Endereço não encontrado. Verifique os dados e tente novamente.', 'danger')
                return redirect(url_for('register'))

            # Cria o usuário com os novos campos
            user = User(
                username=username,
                email=email,
                password=password,
                tipo=tipo,
                endereco=endereco,
                cidade=cidade,
                estado=estado,
                cep=cep,
                latitude=latitude,
                longitude=longitude
            )

            try:
                db.session.add(user)
                db.session.commit()
                flash('Conta criada com sucesso!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Erro ao criar a conta. Tente novamente.', 'danger')
                print(f"Erro ao criar usuário: {e}")  # Log do erro
                return redirect(url_for('register'))

        return render_template('register.html')

    @app.route('/dashboard_doador')  # Rota do dashboard do doador
    @login_required
    def dashboard_doador():
        if current_user.tipo != 'doador':
            return redirect(url_for('index'))
        return render_template('dashboard_doador.html')

    @app.route('/dashboard_receptor')  # Rota do dashboard do receptor
    @login_required
    def dashboard_receptor():
        if current_user.tipo != 'receptor':
            return redirect(url_for('index'))
        return render_template('dashboard_receptor.html')

    def calcular_distancia(lat1, lon1, lat2, lon2):
        # Raio da Terra em quilômetros
        R = 6371.0

        # Converte graus para radianos
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        # Diferença das coordenadas
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        # Fórmula de Haversine
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Distância em quilômetros
        distancia = R * c
        return distancia

    @app.route('/buscar_doadores', methods=['GET', 'POST'])
    @login_required
    def buscar_doadores():
        if current_user.tipo != 'receptor':
            return redirect(url_for('index'))

        if request.method == 'POST':
            # Obter a localização do receptor
            receptor_lat = current_user.latitude
            receptor_lon = current_user.longitude

            # Buscar todos os doadores que fizeram pelo menos uma doação
            doadores = User.query.filter_by(tipo='doador').join(Doacao).distinct().all()

            # Calcular a distância de cada doador
            doadores_proximos = []
            for doador in doadores:
                distancia = calcular_distancia(receptor_lat, receptor_lon, doador.latitude, doador.longitude)
                if distancia <= 50:  # Exemplo: 50 km de distância máxima
                    doadores_proximos.append((doador, distancia))

            # Ordenar por distância
            doadores_proximos.sort(key=lambda x: x[1])

            return render_template('buscar_doadores.html', doadores=doadores_proximos)

        return render_template('buscar_doadores.html')
    
    @app.route('/cadastrar_doacao', methods=['GET', 'POST'])
    @login_required
    def cadastrar_doacao():
        if current_user.tipo != 'doador':
            return redirect(url_for('index'))

        if request.method == 'POST':
            quantidade = request.form.get('quantidade')

            if not quantidade:
                flash('Por favor, insira a quantidade de leite doada.', 'danger')
                return redirect(url_for('cadastrar_doacao'))

            try:
                quantidade = float(quantidade)
                if quantidade <= 0:
                    flash('A quantidade deve ser maior que zero.', 'danger')
                    return redirect(url_for('cadastrar_doacao'))
            except ValueError:
                flash('Quantidade inválida. Insira um número válido.', 'danger')
                return redirect(url_for('cadastrar_doacao'))

            # Cria a nova doação
            nova_doacao = Doacao(
                doador_id=current_user.id,
                quantidade=quantidade
            )

            try:
                db.session.add(nova_doacao)
                db.session.commit()
                flash('Doação cadastrada com sucesso!', 'success')
                return redirect(url_for('dashboard_doador'))
            except Exception as e:
                db.session.rollback()
                flash('Erro ao cadastrar a doação. Tente novamente.', 'danger')
                print(f"Erro ao cadastrar doação: {e}")  # Log do erro
                return redirect(url_for('cadastrar_doacao'))

        return render_template('cadastrar_doacao.html')