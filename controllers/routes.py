from flask import render_template, request, url_for, redirect, flash, session
from markupsafe import Markup #codigo de html no flash message, essa markup
from models.database import db, Game, Usuario, Imagem
from werkzeug.security import generate_password_hash, check_password_hash
import urllib
import json
import uuid
import os #sistema operacional

jogadores = []

jogos = []

gamelist = [{'Título' : 'CS-GO', 'Ano' : 2012, 'Categoria' : 'FPS Online'}]

def init_app(app):
    #Função de middleware para verificar a autentificação do usuário
    @app.before_request
    def check_auth():
        routes = ['login', 'caduser', 'home']
        #Se a rota atual não requer autentificação, permite o acesso

        if request.endpoint in routes or request.path.startswith('/static/'):
            return
        #Se o usuário não estiver autenticado, redirecionar para a página de login
        if 'user_id' not in session:
            return redirect(url_for('login'))


    # Definindo a rota principal
    @app.route('/')
    # Função que será executada ao acessar a rota
    def home():
        # Retorno que será exibido na rota
        return render_template('index.html')
    
    #ROTA DE LOGIN
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = Usuario.query.filter_by(email=email).first()
            if user and check_password_hash(user.password,password): #a primeira esa senha do banco user.password, a segunda e a senha digitado password
                session['user_id'] = user.id
                session['email'] = user.email
                nickname = user.email.split('@')
                flash(f'login bem sucedido! Bem vindo {nickname[0]}!', 'success')
        # Retorno que será exibido na rota
                return redirect(url_for('home'))
            else:
                flash('Falha no login, Verifique seu nome de usuário e senha', 'danger')
        return render_template('login.html')
    
    #ROTA LOGOUT
    @app.route('/logout', methods=['GET', 'POST'])
    def logout():
        session.clear()
        return redirect(url_for('home'))
    
    #ROTA DE CADASTRO DE USUARIO
    @app.route('/caduser', methods=['GET', 'POST'])
    def caduser():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = Usuario.query.filter_by(email=email).first()
            if user:
                msg = Markup("Usuário já cadastrado. Faça <a href='/login'>login</a>.")
                #print (email, password)
                flash(msg, 'danger')
                return redirect(url_for('caduser'))
            
            else:
                hashed_password = generate_password_hash(password, method='scrypt')
                new_user = Usuario(email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()

                flash('Registro realizado com sucesso! Faça o login','success')
                return redirect(url_for('login'))
            
        # Retorno que será exibido na rota
        return render_template('caduser.html')

    @app.route('/games', methods=['GET', 'POST'])
    def games():
        game = gamelist[0]
        
        if request.method == 'POST':
            if request.form.get('jogador'):
                jogadores.append(request.form.get('jogador'))
    
            if request.form.get('jogos'):
                jogos.append(request.form.get('jogos'))
        return render_template('games.html', game=game, jogos=jogos, jogadores=jogadores)

    @app.route('/cadgames', methods=['GET', 'POST'])
    def cadgames():
        if request.method == 'POST':
            if request.form.get('titulo') and request.form.get('ano') and request.form.get('categoria'):
                gamelist.append({'Título': request.form.get('titulo'), 'Ano' : request.form.get('ano'), 'Categoria' : request.form.get('categoria')})
        
        return render_template('cadgames.html', gamelist=gamelist)

    @app.route('/apigames', methods=['GET','POST'])
    @app.route('/apigames/<int:id>', methods=['GET','POST'])#informa o tipo nesse caso int
    def apigames(id=None): #tem que informa o parametro para a função, o parametro id vai ser  opcional

        url = 'https://www.freetogame.com/api/games'
        res = urllib.request.urlopen(url)
        data= res.read()
        gamesjson = json.loads(data)# pega um conjunto de dados e converte para um dicionario um python

        if id:
            ginfo = []
            for g in gamesjson:
                if g['id'] == id:
                    ginfo = g
                    break
            if ginfo:
                return render_template('gamesinfo.html', ginfo=ginfo)
            else:
                return f'Game com a ID {id} não foi encontrado.'
        else:
            return render_template('apigames.html', gamesjson=gamesjson) 

#criando nosso crud
    @app.route('/estoque', methods=['GET','POST'])
    @app.route('/estoque/delete/<int:id>')
    def estoque(id=None):
        #Excluindo um jogo
        if id:
            game = Game.query.get(id)
            db.session.delete(game)
            db.session.commit()
            return redirect(url_for('estoque'))
        #Cadastrando um novo jogo
        if request.method == 'POST':
            newgame = Game(request.form['titulo'], request.form['ano'], request.form['categoria'], request.form['plataforma'], request.form['preco'], request.form['quantidade'])
            db.session.add(newgame)
            db.session.commit()
            #redirecionei o usuario para mesma rota
            return redirect(url_for('estoque'))
        else:
        #Captura o valor da 'page' que foi passado pelo metódo GET
        #Defina como padrão o valor 1 e o tipo inteiro
            page = request.args.get('page', 1, type=int)
        #Valor padrão de regisros por página (definimos 3)
            per_page = 3
            games_page = Game.query.paginate(page=page,per_page=per_page)
            return render_template('estoque.html', gamesestoque = games_page)
        
    #   CRUD - Edição de dados
    @app.route('/edit/<int:id>', methods=['GET', 'POST'])
    def edit(id):
        g = Game.query.get(id)
        # Editando o jogo com as informações do formulário
        if request.method == 'POST':
            g.titulo = request.form['titulo']
            g.ano = request.form['ano']
            g.categoria = request.form['categoria']
            g.plataforma = request.form['plataforma']
            g.preco = request.form['preco']
            g.quantidade = request.form['quantidade']
            db.session.commit()
            return redirect(url_for('estoque'))
        return render_template('editgame.html', g=g)
    
    #DEFININDO TIPOS DE ARQUIVOS PERMITIDOS
    FILE_TYPES = set(['png', 'jpg', 'jpeg', 'gif'])
    def arquivos_permitidos(filename):
        return '.' in filename and filename.rsplit('.',1)[1].lower() in FILE_TYPES  # faz um corte no nome exemplo (game.jpg) divide o nome em dois, game[fica em indice 0] e jpg[no indice 1]

    #ROTA PARA GALERIA
    @app.route('/galeria',methods=['GET', 'POST'])
    def galeria():
        #Selecionando os nomes dos arquivos de imagens no banco
        imagens = Imagem.query.all() #memorizar todos os metodos do banco para prova
        if request.method == 'POST':
            # Captura o arquivo vindo do formulário
            file = request.files['file']
            #verifica se a extensão do arquivo é permitido
            if not arquivos_permitidos(file.filename):
                flash("Arquivo inválido! Utilize tipos de arquivos referentes a imagem", 'danger')
                return redirect(request.url)
            #Definir um nome aleatório para o arquivo
            filename = str(uuid.uuid4())

            #gravando informações do arquivo no banco
            img = Imagem(filename)
            db.session.add(img)
            db.session.commit()

            #Salva o arquivo na pasta de uploads
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            flash("Imagem enviada com sucesso!", 'success')
            return redirect(url_for('galeria'))
        return render_template('galeria.html', imagens=imagens)