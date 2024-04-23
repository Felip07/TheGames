# Importando o Flask na aplicação
from flask import Flask, render_template
from controllers import routes
import os #ajuda a achar o diretorio do banco
from models.database import db

# Carregando o Flask na variável app
app = Flask(__name__, template_folder='views')

# Iniciando a função de rotas init_app passando o Flask como parâmetro
routes.init_app(app)

#Permite ler o diretório absoluto de um determinado arquivo
dir = os.path.abspath(os.path.dirname(__file__)) 

#Passando o diretório para o SQLAlchemy, nome do banco games.sqlite3
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(dir, 'models/games.sqlite3')

#Definindo a SECRET KEY para as Flash Messages
app.config['SECRET_KEY'] = 'thegamessecret'

# Define o tempo de duraçãpo da sessão
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

#Define pasta que receberá arquivos de upload 
app.config['UPLOAD_FOLDER'] = 'static/uploads'

#Definindo o tamanho máximo de um arquivo de upload
app.config['MAX_CONTENT_LENGHT'] = 16 *1024 * 1024 #byte, kbytes, megabytes

# Se for executado diretamente pelo interpretador (arquivo principal)
if __name__ == '__main__':

    #Verifica no inicio da aplicação se o BD já existe. Caso contrário ele criará o BD.
    db.init_app(app=app)
    with app.test_request_context():
        db.create_all()

    # Rodando a aplicação no localhost, porta 5000, modo debug ativado
    app.run(host='localhost', port=5000, debug=True)