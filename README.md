Команда зі створення образа:
```
docker build -t mind-card_notes .
```
Перевірка IP хостової машини в мережі docker:
```
ip a | grep docker
```
Перевірка, який IP слухає локальна mySQL:
```
mysql -u mysqluser -p -e "SHOW VARIABLES LIKE 'bind_address';"
```
Встановлення заданих IP з яких буде слухати mySQL:
```
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```
В розділі [mysqld] прописати:
```
bind-address            = 0.0.0.0
```
Перевірка IP хостової машини в мережі docker:
```
ip a | grep docker
```
Прописати в .env цю адресу. На цю адресу піде додаток з контейнера шукати mySQL:
```
DB_HOST=172.17.0.1
```

Команда зі створення контейнера:
```
docker run -d \                       
  -p 8000:8000 \
  --env-file .env \
  --name mind-notes-app \
  mind-card_notes:latest
```
Ephemeral Storage
Ця файлова система повністю прив'язана до життєвого циклу конкретного контейнера:
Якщо ти просто зупиниш контейнер (docker stop) і запустиш знову (docker start), дані збережуться.
Але якщо ти видалиш контейнер (docker rm) або перезобережеш/перезапустиш його, усі файли, які додаток записав усередину контейнера, зникнуть назавжди.
