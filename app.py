<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocFlow - Análise de Documentos</title>
    <!-- Tailwind CSS para estilização -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">

    <div class="bg-slate-800 border border-slate-700 p-8 rounded-2xl shadow-xl w-full max-w-xl">
        <h1 class="text-3xl font-bold mb-2 text-center bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
            DocFlow IA
        </h1>
        <p class="text-slate-400 text-sm text-center mb-6">
            Envie um documento PDF para classificação e extração automática de informações.
        </p>
        
        <div class="mb-6">
            <label class="block text-sm font-medium text-slate-300 mb-2">Selecione o arquivo:</label>
            <input type="file" id="arquivoPdf" accept=".pdf,.doc,.docx,.txt,.png,.jpg" 
                class="w-full text-sm text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer cursor-pointer bg-slate-900/50 border border-slate-700 rounded-xl p-2 transition"/>
        </div>

        <button onclick="processarDocumento()" id="btnProcessar"
            class="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-xl font-semibold transition shadow-lg flex items-center justify-center">
            Analisar Documento
        </button>

        <div class="mt-8">
            <h2 class="text-lg font-semibold text-slate-300 mb-2">Resultado da Análise:</h2>
            <div id="resultado" class="w-full min-h-[150px] bg-slate-900/80 border border-slate-700 rounded-xl p-4 text-slate-300 text-sm overflow-y-auto whitespace-pre-wrap hidden">
                Aguardando o envio do documento...
            </div>
        </div>
    </div>

    <script>
        async function processarDocumento() {
            const inputArquivo = document.getElementById('arquivoPdf');
            const resultadoDiv = document.getElementById('resultado');
            const btnProcessar = document.getElementById('btnProcessar');

            if (inputArquivo.files.length === 0) {
                alert('Por favor, selecione um arquivo primeiro.');
                return;
            }

            const formData = new FormData();
            formData.append('file', inputArquivo.files[0]);

            resultadoDiv.classList.remove('hidden');
            resultadoDiv.textContent = 'Analisando documento com Inteligência Artificial, por favor aguarde...';
            btnProcessar.disabled = true;
            btnProcessar.classList.add('opacity-50', 'cursor-not-allowed');

            try {
                // Utiliza rota relativa para funcionar perfeitamente no Render
                const response = await fetch('/api/analisar', {
                    method: 'POST',
                    body: formData
                });

                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    const textError = await response.text();
                    throw new Error(`Erro do Servidor (${response.status}): ${textError.slice(0, 100)}`);
                }

                if (!response.ok) {
                    throw new Error(data.error || 'Erro desconhecido ao processar.');
                }

                // Exibe o resultado formatado gerado pela IA
                resultadoDiv.textContent = data.resultado;

            } catch (error) {
                console.error(error);
                resultadoDiv.textContent = `Erro: ${error.message}`;
            } finally {
                btnProcessar.disabled = false;
                btnProcessar.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }
    </script>
</body>
</html>
