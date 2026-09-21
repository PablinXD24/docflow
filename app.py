import os
import tempfile
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Configura a chave da API do Google Gemini
api_key = os.environ.get("GEMIN_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analisar", methods=["POST"])
def analisar():
    # Verifica se um arquivo foi enviado na requisição
    if 'documento' not in request.files:
        return jsonify({"error": "Nenhum arquivo foi enviado."}), 400
    
    file = request.files['documento']
    
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    temp_file_path = None
    uploaded_file_ref = None

    try:
        # Salva temporariamente no servidor para envio à API do Google
        fd, temp_file_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        os.close(fd)
        file.save(temp_file_path)

        # Faz o upload do arquivo para a API do Google (suporta PDF, imagens, etc.)
        uploaded_file_ref = client.files.upload(file=temp_file_path)

        # Prompt estruturado para extração das informações principais
        prompt = (
            "Você é um especialista em classificação e tratamento de documentos empresariais/legais. "
            "Analise detalhadamente o documento anexado e forneça: "
            "1. **Classificação/Tipo do Documento** (Ex: Contrato, Fatura, Relatório, RG, etc.). "
            "2. **Principais Informações** (Resumo executivo, datas importantes, valores e partes envolvidas). "
            "3. **Pendências ou Recomendações de Tratamento** (Próximos passos necessários)."
        )

        # Chamada ao modelo Gemini 2.5 Flash com suporte nativo a documentos
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, uploaded_file_ref]
        )

        return jsonify({"resultado": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Limpeza de arquivos temporários locais
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Limpeza opcional do arquivo na API do Google se necessário
        if uploaded_file_ref:
            try:
                client.files.delete(name=uploaded_file_ref.name)
            except:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
