# Use uma imagem Python leve e oficial
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /usr/src/app

# --- Instalação de Dependências ---
# Copia apenas o arquivo de requerimentos primeiro para aproveitar o cache do Docker.
# Esta camada só será reconstruída se o requirements.txt mudar.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# --- Cópia do Código do Spider ---
# Copia todo o diretório do projeto para dentro do container
COPY . .

# --- Comando de Execução ---
# Define o comando padrão para rodar o sitemap spider quando o container iniciar.
# Este é o comando que você usaria no seu terminal.
CMD ["scrapy", "crawl", "bistek_sitemap_spider"]

