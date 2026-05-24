from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# --- Configurações Principais ---
app.config['SECRET_KEY'] = 'uma_chave_secreta_e_segura' # Necessária para usar flash()

# Define onde salvar as fotos (static/fotos) e os arquivos (static/arquivos)
FOTOS_FOLDER = os.path.join(os.getcwd(), 'static', 'fotos')
ARQUIVOS_FOLDER = os.path.join(os.getcwd(), 'static', 'arquivos')
app.config['FOTOS_FOLDER'] = FOTOS_FOLDER
app.config['ARQUIVOS_FOLDER'] = ARQUIVOS_FOLDER

# URI do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arquivo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cria as pastas necessárias automaticamente se elas não existirem
os.makedirs(FOTOS_FOLDER, exist_ok=True)
os.makedirs(ARQUIVOS_FOLDER, exist_ok=True)

# Define as extensões de arquivo permitidas para a foto
ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

db = SQLAlchemy(app)

# --- Modelo do Banco de Dados ---
# Adicionamos um novo campo 'caminho_foto'
class ArquivoCompleto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False) # Título
    caminho_arquivo = db.Column(db.String(255), nullable=False) # Nome do arquivo principal (.pdf, .zip, etc)
    caminho_foto = db.Column(db.String(255), nullable=True) # Nome da foto de capa (.jpg, .png, etc)

with app.app_context():
    db.create_all()


# --- Rotas Principais ---

@app.route('/')
def home():
    # Pega o termo de busca enviado pela URL (se não houver, fica None)
    termo_busca = request.args.get('q', '').strip()
    
    if termo_busca:
        # Busca apenas os arquivos que contenham o termo no nome (Ignora maiúsculas/minúsculas no SQLite)
        registros = ArquivoCompleto.query.filter(ArquivoCompleto.nome.like(f'%{termo_busca}%')).all()
    else:
        # Se não houver busca, exibe todos normalmente
        registros = ArquivoCompleto.query.all()
        
    return render_template('home.html', registros=registros)

@app.route('/admin/arquivos/novos/', methods=['GET', 'POST'])
def admin_arquivos():
    if request.method == 'POST':
        # 1. Pega o título/nome
        nome = request.form['nome']
        
        # 2. Pega os dois arquivos enviados
        file_arquivo = request.files.get('arquivo_principal')
        file_foto = request.files.get('arquivo_foto')

        # Validação básica
        if not nome or not file_arquivo:
            flash('Título e Arquivo Principal são obrigatórios!', 'danger')
            return redirect(url_for('admin_arquivos'))

        # Inicializa os nomes como vazios para o banco
        filename_arquivo = ''
        filename_foto = ''

        # --- Processar o ARQUIVO PRINCIPAL (qualquer extensão) ---
        if file_arquivo and file_arquivo.filename != '':
            filename_arquivo = secure_filename(file_arquivo.filename)
            file_arquivo.save(os.path.join(app.config['ARQUIVOS_FOLDER'], filename_arquivo))

        # --- Processar a FOTO/IMAGEM DE CAPA (somente extensões permitidas) ---
        if file_foto and file_foto.filename != '':
            if allowed_file(file_foto.filename, ALLOWED_PHOTO_EXTENSIONS):
                filename_foto = secure_filename(file_foto.filename)
                file_foto.save(os.path.join(app.config['FOTOS_FOLDER'], filename_foto))
            else:
                flash('A foto deve ser uma imagem válida (jpg, jpeg, png, gif)! O registro foi criado sem foto.', 'warning')
        
        # 3. Salva no Banco de Dados
        novo_registro = ArquivoCompleto(
            nome=nome, 
            caminho_arquivo=filename_arquivo, 
            caminho_foto=filename_foto
        )
        db.session.add(novo_registro)
        db.session.commit()
        
        flash(f'Registro "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('admin_arquivos')) 
    
    registros = ArquivoCompleto.query.all()
    return render_template('admin/arquivos.html', registros=registros)


# --- Rotas Extras para Servir Arquivos e Fotos ---

# Rota para baixar/visualizar o arquivo principal (doc, pdf, zip, etc)
@app.route('/static/arquivos/<filename>')
def serve_arquivo(filename):
    return send_from_directory(app.config['ARQUIVOS_FOLDER'], filename)

# Rota para exibir as fotos de capa
@app.route('/static/fotos/<filename>')
def serve_foto(filename):
    return send_from_directory(app.config['FOTOS_FOLDER'], filename)

@app.route('/sobre-min/')
def sobre_mim():
    return render_template('sobre-min.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)