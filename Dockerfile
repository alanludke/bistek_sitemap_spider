FROM python:3.9-slim

# Define o diretório de trabalho da imagem Docker
WORKDIR /app

# Define a variável com o nome do diretório
ARG SPIDER_DIR=bistek_sitemap_spider

# Copia o arquivo requirements.txt para o diretório de trabalho
COPY $SPIDER_DIR $SPIDER_DIR

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r $SPIDER_DIR/requirements.txt

# Copia o código-fonte do projeto para o diretório de trabalho
COPY common common

# Instala o pacote 'common' usando o arquivo setup.py
RUN python -m pip install --no-cache-dir -e common

# Define o diretório de trabalho específico
WORKDIR /app/$SPIDER_DIR

# Define o comando padrão a ser executado quando o contêiner for iniciado
CMD ["python", "app.py"]
