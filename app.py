import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# A chave da API será lida das variáveis de ambiente do Render
api_key = os.environ.get("GEMIN_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analisar", methods=["POST"])
def analisar():
    data = request.json
    texto_doc = data.get("texto", "")
    
    if not texto_doc:
        return jsonify({"error": "Nenhum texto foi enviado."}), 400

    try:
        # Chamada oficial da SDK do Google GenAI
        prompt = (
            "Você é um assistente especialista em classificação e tratamento de documentos. "
            "Analise o texto abaixo e forneça: "
            "1. Tipo/Classificação do Documento. "
            "2. Principais Informações (Resumo executivo, datas, valores ou partes envolvidas). "
            "3. Status de Tratamento (Recomendações ou pendências).\n\n"
            f"Texto do documento:\n{texto_doc}"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        return jsonify({"resultado": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
