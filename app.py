import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Configura a API do Google GenAI com a chave do ambiente
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analisar", methods=["POST"])
def analisar():
    if "arquivo" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files["arquivo"]
    
    if file.filename == "":
        return jsonify({"error": "Nome de arquivo inválido"}), 400

    try:
        file_bytes = file.read()
        mime_type = file.content_type or "application/pdf"

        # Chamada utilizando o SDK do Google GenAI com o modelo gemini-1.5-flash (mais estável)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                ),
                "Analise este documento. Faça uma classificação do tipo de documento e extraia as principais informações em tópicos claros (ex: Resumo, Dados Principais, Prazos/Valores se houver)."
            ]
        )

        return jsonify({"resultado": response.text})

    except Exception as e:
        # Imprime o erro completo no log do Render para auditoria
        print(f"Erro interno no servidor: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
