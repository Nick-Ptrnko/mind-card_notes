
# 1. Використовуємо легку версію Python
FROM python:3.11-slim

# 2. Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# 3. Копіюємо файл із залежностями та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копіюємо вміст теки з Dockerfile у контейнер
COPY . .

# 5. Expose port to the host
EXPOSE 8000

# 6. Команда для запуску скрипта
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
