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
    data = request.get_json()

    if not data or 'projeto_id' not in data or 'descricao' not in data or 'due_date' not in data:
        return jsonify({'error': 'Dados inválidos!'}), 400

    try:
        nova_atividade = Atividade(
            projeto_id=data['projeto_id'],
            descricao=data['descricao'],
            data_vencimento=datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        )
        db.session.add(nova_atividade)
        db.session.commit()
        return jsonify({"message": "Atividade cadastrada com sucesso!"}), 201
    except Exception as e:
        db.session.rollback()  # Reverte qualquer alteração em caso de erro
        return jsonify({'error': str(e)}), 500  # Retorna o erro caso ocorra


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

@app.route('/projetos', methods=['GET'])
def get_projetos():
    projetos = Projeto.query.all()
    projetos_data = []
    
    for projeto in projetos:
        atividades = Atividade.query.filter_by(projeto_id=projeto.id).all()  # Obtendo as atividades do projeto
        atividades_data = [{'description': atividade.descricao, 'due_date': atividade.data_vencimento.isoformat()} for atividade in atividades]
        
        projetos_data.append({
            'id': projeto.id,
            'nome': projeto.nome,
            'descricao': projeto.descricao,
            'tecnologias': projeto.tecnologias,
            'data_inicio': projeto.data_inicio.isoformat(),  # Converte para ISO format
            'activities': atividades_data  # Adicionando as atividades ao projeto
        })
    
    return jsonify(projetos_data)

@app.route('/projetos/<int:id>', methods=['DELETE'])
def delete_projeto(id):
    projeto = Projeto.query.get(id)
    if not projeto:
        return jsonify({'error': 'Projeto não encontrado!'}), 404

    try:
        db.session.delete(projeto)
        db.session.commit()
        return jsonify({'message': 'Projeto excluído com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()  # Reverte qualquer alteração em caso de erro
        return jsonify({'error': str(e)}), 500  # Retorna o erro caso ocorra

@app.route('/atividades', methods=['GET'])
def listar_atividades():
    atividades = Atividade.query.all()
    return jsonify([{
        'id': a.id,
        'projeto_id': a.projeto_id,
        'descricao': a.descricao,
        'data_vencimento': a.data_vencimento.isoformat()
    } for a in atividades])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco se não existirem
    app.run(debug=True)
