FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la aplicación
COPY . .

# Copiar script de espera
COPY wait-for-db.py /wait-for-db.py
RUN chmod +x /wait-for-db.py

# Exponer el puerto
EXPOSE 8080

# Comando para ejecutar la app con espera a MySQL
CMD ["python", "/wait-for-db.py", "db", "python", "basurero.py"]
