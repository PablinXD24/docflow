import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# Configura a API do Google GenAI com a chave de ambiente do Render
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analisar', methods=['POST'])
def analisar():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nome de arquivo inválido'}), 400

        file_bytes = file.read()
        mime_type = file.content_type or 'application/pdf'

# Chamada para a API do Gemini solicitando texto limpo sem formatações Markdown
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                ),
                'Analise este documento e extraia as principais informações (Resumo, Dados Principais, Valores e Prazos). IMPORTANTE: Responda em texto corrido ou tópicos simples, sem usar nenhum caractere de formatação markdown, sem asteriscos, sem negritos e sem hashtags.'
            ]
        )

        return jsonify({
            'status': 'sucesso',
            'resultado': response.text,
            'nome_arquivo': file.filename
        }), 200

    except Exception as e:
        print(f"Erro no servidor: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
