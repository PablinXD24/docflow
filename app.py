import os
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
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

# Chave e Endpoints do TMDb (The Movie Database) para Busca de Filmes
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "1f54bd990f1cdfb230adb312546d665d") # Chave pública padrão de testes
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/filmes/buscar', methods=['GET'])
def buscar_filmes():
    query = request.args.get('q', '').strip()
    if not query:
        # Se não houver termo digitado, retorna os filmes populares do momento
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=pt-BR&page=1"
    else:
        # Pesquisa personalizada por nome do filme
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=pt-BR&query={requests.utils.quote(query)}&page=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        resultados = []
        for item in data.get('results', []):
            poster_path = item.get('poster_path')
            poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=Sem+Poster"
            resultados.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'release_date': item.get('release_date', '')[:4],
                'poster_url': poster_url,
                'overview': item.get('overview', '')
            })
        return jsonify({'results': resultados})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Limpeza caso o modelo retorne blocos markdown ```json ... ```
        if texto_resposta.startswith("```"):
            texto_resposta = texto_resposta.split("```")[1]
            if texto_resposta.startswith("json"):
                texto_resposta = texto_resposta[4:]
        texto_resposta = texto_resposta.strip()
        
        import json
        recomendacoes_ia = json.loads(texto_resposta)
        
        # Para cada recomendação da IA, buscamos o pôster oficial correspondente via TMDb
        recomendacoes_finais = []
        for rec in recomendacoes_ia:
            titulo_rec = rec.get('titulo')
            motivo = rec.get('motivo')
            
            poster_url = "https://via.placeholder.com/500x750?text=Poster+Indisponivel"
            try:
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=pt-BR&query={requests.utils.quote(titulo_rec)}"
                res_tmdb = requests.get(search_url, timeout=5).json()
                if res_tmdb.get('results'):
                    p_path = res_tmdb['results'][0].get('poster_path')
                    if p_path:
                        poster_url = f"{TMDB_IMAGE_BASE}{p_path}"
            except:
                pass
                
            recomendacoes_finais.append({
                'titulo': titulo_rec,
                'motivo': motivo,
                'poster_url': poster_url
            })
            
        return jsonify({'recomendacoes': recomendacoes_finais})
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar recomendações: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
