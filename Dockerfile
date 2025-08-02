# 🧠 Base leve e segura
FROM python:3.11-slim

# 🛠️ Evita problemas com timezone e arquivos corrompidos
ENV TZ=America/Sao_Paulo
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 📁 Define diretório de trabalho
WORKDIR /app

# ⚙️ Atualiza dependências do sistema e instala pacotes essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 📦 Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 🧬 Copia código-fonte para dentro do container
COPY . .

# 🎯 Define o script principal dinamicamente com ENTRYPOINT se desejar
CMD ["python", "suimonitor.py"]
