from charlie_voice import falar
import sys

mensagem_tipo = sys.argv[1] if len(sys.argv) > 1 else "neutra"

mensagens = {
    "manha": "Bom dia, comandante. Hoje é um novo dia para vencer. Vamos começar com foco total.",
    "noite": "Boa noite, comandante. CharlieCore finalizou as operações de hoje. Até breve.",
    "motivacional": "Você é mais forte do que pensa. Avance com coragem, a vitória está logo à frente.",
    "alerta": "Atenção total. Um novo desafio se aproxima.",
    "urgente": "Situação crítica detectada. CharlieCore ativando o modo de resposta imediata.",
    "neutra": "CharlieCore pronta para operar. Comando reconhecido.",
}

emocao_por_tipo = {
    "manha": "alegre",
    "noite": "suave",
    "motivacional": "inspirador",
    "alerta": "urgente",
    "urgente": "urgente",
    "neutra": "neutra"
}

texto = mensagens.get(mensagem_tipo, mensagens["neutra"])
emocao = emocao_por_tipo.get(mensagem_tipo, "neutra")

falar(texto, emocao)
