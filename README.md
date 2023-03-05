# FOODGRAM
![yamdb_workflow](https://github.com/Starboy-Shpak/foodgram-project-react/actions/workflows/main.yml/badge.svg)

Foodgram - сайт для создания просмотра и публикации рецептов

Проект доступен по: [ссылке](http://51.250.18.184/)

## Что проект умеет?

Foodgram - предназначен для публикации рецептов различных блюд. В функционал сайта входит публикация, изменение и добавление в избранное рецептов, скачивание списка необходимых продуктов, подписка на авторов.

### Как запустить проект:

```
Файл `.env` для звпуска должен содержать переменные:
```
DEBAG=True/False               # включить или выключить режим отсладки
SECRET_KEY=<key>               # cтандартный ключ, который создается при старте проекта
ALLOWED_HOSTS =[*]             # IP вашего сервера

DB_NAME=postgres               # имя БД
POSTGRES_USER=postgres         # логин для подключения к БД
POSTGRES_PASSWORD=<password>   # пароль для подключения к БД
DB_HOST=db                     # название сервиса (контейнера)
DB_PORT=5432                   # порт для подключения к БД
```
Далее запускаем Docker Compose:
```
docker compose up -d --build
```
Переходим в контейнер "backend":
```
sudo docker exec -it <ID контейнера> bash 
```
Выполняем миграции:
```
python manage.py migrate
```
Создаем суперпользователя:
```
python manage.py createsuperuser
```
Собираем статику:
```
python manage.py collectstatic --no-input
```
Создаем дамп базы данных (нет в текущем репозитории):
```
python manage.py dumpdata > dumpPostrgeSQL.json
```

***
Автор: Вадим Шпак.
Связаться со мной можно в [телеграм](https://t.me/starboy_shpak/)