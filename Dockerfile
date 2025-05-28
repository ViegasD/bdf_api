# Etapa 1: imagem base
FROM python:3.13-slim

# Etapa 2: diretório de trabalho
WORKDIR /app

# Etapa 3: copiar dependências
COPY requirements.txt .

# Etapa 4: instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 5: copiar os arquivos do projeto
COPY . .

# Etapa 6: expor a porta do servidor
EXPOSE 8456

# Etapa 7: comando para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8456"]
