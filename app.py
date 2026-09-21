import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from google import genai

app = Flask(__name__)

# Configuração da chave de API do Gemini usando o novo cliente
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "SUA_CHAVE_API_AQUI")
client = genai.Client(api_key=GEMINI_API_KEY)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analisar', methods=['POST'])
def analisar_documento():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Faz o upload do arquivo usando a File API do novo SDK
            uploaded_file = client.files.upload(file=filepath)
            
            prompt = (
                "Você é um assistente especialista em análise de documentos e contratos. "
                "Analise detalhadamente este documento e forneça um resumo estruturado. "
                "OBRIGATÓRIO: Logo no início da resposta, liste destacando em **negrito** os dados e informações mais importantes, "
                "tais como: **Nome do Contratado / Responsável**, **Empresa**, **CNPJ / CPF**, **Data de Nascimento** e **Data do Documento**. "
                "Em seguida, apresente os demais detalhes, cláusulas e o contexto geral do documento de forma clara e limpa."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[uploaded_file, prompt]
            )
            resultado_texto = response.text
            
            # Remove o arquivo temporário do servidor
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return jsonify({'resultado': resultado_texto})
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
