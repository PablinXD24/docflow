import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai

app = Flask(__name__)

# Lê a chave de ambiente e remove espaços acidentais
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()

if not GEMINI_API_KEY:
    print("AVISO: Chave de API do Gemini não encontrada nas variáveis de ambiente!")
else:
    print(f"Chave carregada com sucesso (Inicia com: {GEMINI_API_KEY[:6]}...)")

genai.configure(api_key=GEMINI_API_KEY)

# Configuração do modelo Gemini
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

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
            uploaded_file = genai.upload_file(filepath)
            
            prompt = (
                "Você é um assistente especialista em análise de documentos e contratos. "
                "Analise detalhadamente este documento e forneça um resumo estruturado. "
                "OBRIGATÓRIO: Logo no início da resposta, liste destacando em **negrito** os dados e informações mais importantes, "
                "tais como: **Nome do Contratado / Responsável**, **Empresa**, **CNPJ / CPF**, **Data de Nascimento** e **Data do Documento**. "
                "Em seguida, apresente os demais detalhes, cláusulas e o contexto geral do documento de forma clara e limpa."
            )
            
            response = model.generate_content([uploaded_file, prompt])
            resultado_texto = response.text
            
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
