import os
import requests
from flask import Flask, render_template, request, jsonify
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
    "temperature": 0.4,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

# Chave pública do TMDb configurada para demonstração robusta do catálogo de filmes
TMDB_API_KEY = "c121404c50117466133177651c6c06fa" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/filmes/populares', methods=['GET'])
def buscar_filmes_populares():
    """Busca filmes populares e em alta na API do TMDb"""
    try:
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=pt-BR&page=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        filmes = []
        if 'results' in data:
            for item in data['results']:
                poster_path = item.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://placehold.co/500x750/1a1a1a/ffffff?text=Sem+Poster"
                filmes.append({
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'overview': item.get('overview', 'Sem sinopse disponível.'),
                    'release_date': item.get('release_date', ''),
                    'vote_average': item.get('vote_average', 0),
                    'poster_path': poster_url
                })
        return jsonify({'filmes': filmes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filmes/buscar', methods=['GET'])
def pesquisar_filmes():
    """Pesquisa filmes no TMDb por termo"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'filmes': []})
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=pt-BR&query={requests.utils.quote(query)}&page=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        filmes = []
        if 'results' in data:
            for item in data['results']:
                poster_path = item.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://placehold.co/500x750/1a1a1a/ffffff?text=Sem+Poster"
                filmes.append({
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'overview': item.get('overview', 'Sem sinopse disponível.'),
                    'release_date': item.get('release_date', ''),
                    'vote_average': item.get('vote_average', 0),
                    'poster_path': poster_url
                })
        return jsonify({'filmes': filmes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recomendar', methods=['POST'])
def gerar_recomendacoes():
    """Recebe exatamente 3 filmes escolhidos e usa a IA para gerar 5 recomendações personalizadas com cartazes"""
    dados = request.get_json()
    filmes_escolhidos = dados.get('filmes', [])
    
    if len(filmes_escolhidos) != 3:
        return jsonify({'error': 'Você deve selecionar exatamente 3 filmes.'}), 400
    
    titulos = [f['title'] for f in filmes_escolhidos]
    
    prompt = (
        f"O usuário escolheu os seguintes 3 filmes favoritos: {titulos[0]}, {titulos[1]} e {titulos[2]}. "
        "Com base no estilo, gênero, diretores, tom e temática desses 3 filmes, atue como um crítico de cinema especialista e "
        "recomende exatamente 5 novos filmes imperdíveis para ele assistir.\n\n"
        "OBRIGATÓRIO: Responda estritamente no seguinte formato JSON puro (sem marcações de markdown externas além do JSON, sem texto livre fora do JSON):\n"
        "{\n"
        '  "analise_perfil": "Breve parágrafo analítico explicando o porquê da seleção combinada destes 3 filmes.",\n'
        '  "recomendacoes": [\n'
        "    {\n"
        '      "titulo": "Nome Exato do Filme Recomendado",\n'
        '      "motivo": "Por que o usuário vai gostar com base nos seus favoritos",\n'
        '      "genero": "Gêneros principais",\n'
        '      "ano": "Ano de lançamento"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    
    try:
        response = model.generate_content(prompt)
        texto_resposta = response.text.strip()
        
        # Limpeza caso o modelo adicione blocos ```json ... ```
        if texto_resposta.startswith("```json"):
            texto_resposta = texto_resposta[7:]
        if texto_resposta.endswith("```"):
            texto_resposta = texto_resposta[:-3]
        texto_resposta = texto_resposta.strip()
        
        import json
        resultado_json = json.loads(texto_resposta)
        
        # Para cada filme recomendado pela IA, buscamos o pôster oficial correspondente no TMDb
        for rec in resultado_json.get('recomendacoes', []):
            titulo_busca = rec['titulo']
            try:
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=pt-BR&query={requests.utils.quote(titulo_busca)}&page=1"
                resp_search = requests.get(search_url, timeout=5).json()
                results = resp_search.get('results', [])
                if results:
                    best_match = results[0]
                    p_path = best_match.get('poster_path')
                    rec['poster_path'] = f"https://image.tmdb.org/t/p/w500{p_path}" if p_path else "https://placehold.co/500x750/1a1a1a/ffffff?text=Capa+Indisponivel"
                    rec['vote_average'] = best_match.get('vote_average', 8.0)
                    if not rec.get('ano') and best_match.get('release_date'):
                        rec['ano'] = best_match.get('release_date').split('-')[0]
                else:
                    rec['poster_path'] = "https://placehold.co/500x750/1a1a1a/ffffff?text=Capa+Indisponivel"
            except:
                rec['poster_path'] = "https://placehold.co/500x750/1a1a1a/ffffff?text=Capa+Indisponivel"

        return jsonify(resultado_json)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar recomendações com a IA: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
