import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configuração da Chave Gemini
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={"temperature": 0.7, "max_output_tokens": 2048}
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recomendar', methods=['POST'])
def recomendar_filmes():
    dados = request.get_json() or {}
    filmes_escolhidos = dados.get('filmes', [])
    
    if len(filmes_escolhidos) < 3:
        return jsonify({'error': 'Selecione exatamente 3 filmes.'}), 400
        
    nomes_filmes = [f['title'] for f in filmes_escolhidos]
    
    prompt = (
        f"O usuário escolheu os seguintes 3 filmes favoritos: {', '.join(nomes_filmes)}. "
        "Com base no estilo, gênero, diretores e temática desses filmes, atue como um especialista em cinema "
        "e indique exatamente 5 novos filmes recomendados. "
        "Retorne sua resposta estritamente no formato JSON puro (sem marcação markdown extra se possível, ou em um bloco limpo) contendo uma lista com os objetos no seguinte formato exato para cada recomendação:\n"
        "[\n"
        "  {\"titulo\": \"Nome do Filme 1\", \"motivo\": \"Breve explicação do porquê foi recomendado\"},\n"
        "  ...\n"
        "]"
    )
    
    try:
        response = model.generate_content(prompt)
        texto_resposta = response.text.strip()
        
        if texto_resposta.startswith("```"):
            texto_resposta = texto_resposta.split("```")[1]
            if texto_resposta.startswith("json"):
                texto_resposta = texto_resposta[4:]
        texto_resposta = texto_resposta.strip()
        
        import json
        recomendacoes_ia = json.loads(texto_resposta)
        return jsonify({'recomendacoes': recomendacoes_ia})
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar recomendações: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
