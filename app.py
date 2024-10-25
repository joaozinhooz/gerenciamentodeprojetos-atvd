from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'  # Caminho do seu banco de dados
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo do Projeto
class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tecnologias = db.Column(db.String(200), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Projeto {self.nome}>'

# Modelo da Atividade
class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)

    projeto = db.relationship('Projeto', backref='atividades')

    def __repr__(self):
        return f'<Atividade {self.descricao}>'

@app.route('/cadastrarprojeto', methods=['POST'])
def cadastrar_projeto():
    data = request.get_json()

    if not data or 'projectName' not in data or 'projectDescription' not in data or 'technologies' not in data or 'startDate' not in data:
        return jsonify({'error': 'Dados inválidos!'}), 400

    try:
        novo_projeto = Projeto(
            nome=data['projectName'],
            descricao=data['projectDescription'],
            tecnologias=data['technologies'],
            data_inicio=datetime.strptime(data['startDate'], '%Y-%m-%d').date()
        )

        db.session.add(novo_projeto)
        db.session.commit()

        return jsonify({'message': 'Projeto cadastrado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna o erro caso ocorra

@app.route('/cadastraratividade', methods=['POST'])
def cadastrar_atividade():
    data = request.json

    projeto_id = data.get('projeto_id')
    descricao = data.get('descricao')
    due_date = data.get('due_date')

    # Adicione depuração para ver os dados recebidos
    print(f"Dados recebidos: projeto_id={projeto_id}, descricao={descricao}, due_date={due_date}")

    if not projeto_id:
        projeto_id = 1  # ID padrão se não fornecido
    if not descricao:
        descricao = "Descrição padrão"  # Usar descrição padrão
    if not due_date:
        due_date = datetime.today().date().isoformat()  # Data atual como padrão

    try:
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    except ValueError:
        due_date = datetime.today().date()  # Data atual em caso de erro

    nova_atividade = Atividade(projeto_id=projeto_id, descricao=descricao, data_vencimento=due_date)

    try:
        db.session.add(nova_atividade)
        db.session.commit()
        return jsonify({"message": "Atividade cadastrada com sucesso."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@app.route('/')
def home():
    return send_from_directory('static', 'home.html')

@app.route('/cadastrarprojeto')
def cadastrar_projeto_page():
    return send_from_directory('static', 'cadastrarprojeto.html')

@app.route('/cadastraratividade')
def cadastrar_atividade_page():
    return send_from_directory('static', 'cadastraratividade.html')

@app.route('/config')
def config_page():
    return send_from_directory('static', 'config.html')

# Rota para listar projetos com suas atividades
@app.route('/projetos', methods=['GET'])
def listar_projetos():
    projetos = Projeto.query.all()
    projetos_dados = []
    
    for projeto in projetos:
        atividades = [{'id': atividade.id, 'descricao': atividade.descricao, 'due_date': atividade.data_vencimento.isoformat()} for atividade in projeto.atividades]
        projetos_dados.append({
            'id': projeto.id,
            'nome': projeto.nome,
            'descricao': projeto.descricao,
            'tecnologias': projeto.tecnologias,
            'data_inicio': projeto.data_inicio.isoformat(),
            'atividades': atividades  # Inclui as atividades associadas ao projeto
        })
    
    return jsonify(projetos_dados)

@app.route('/projetos/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    projeto = Projeto.query.get(project_id)
    
    if not projeto:
        abort(404, description="Projeto não encontrado")

    # Excluir atividades relacionadas ao projeto
    atividades = Atividade.query.filter_by(projeto_id=project_id).all()
    for atividade in atividades:
        db.session.delete(atividade)

    # Excluir o projeto
    db.session.delete(projeto)
    db.session.commit()

    return jsonify({"message": "Projeto e atividades deletados com sucesso!"}), 200

@app.route('/atividades', methods=['GET'])
def get_atividades():
    atividades = Atividade.query.all()  # Recupera todas as atividades
    atividades_list = [{'id': a.id, 'descricao': a.descricao, 'due_date': a.due_date, 'projeto_id': a.projeto_id} for a in atividades]
    return jsonify(atividades_list)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco se não existirem
    app.run(debug=True)
