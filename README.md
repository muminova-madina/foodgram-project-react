# Foodgram
Cервис для публикаций и обмена рецептами.

Авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в покупки, скачивать список покупок. Неавторизованным пользователям доступна регистрация, авторизация, просмотр рецептов других пользователей.

![example branch parameter](https://github.com/madina-zvezda/foodgram-project-react/actions/workflows/yamdb_workflow.yml/badge.svg)
[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat&logo=Django%20REST%20Framework&logoColor=56C0C0&color=008080)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat&logo=PostgreSQL&logoColor=56C0C0&color=008080)](https://www.postgresql.org/)
[![JWT](https://img.shields.io/badge/-JWT-464646?style=flat&color=008080)](https://jwt.io/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat&logo=NGINX&logoColor=56C0C0&color=008080)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat&logo=gunicorn&logoColor=56C0C0&color=008080)](https://gunicorn.org/)
[![Docker](https://img.shields.io/badge/-Docker-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker-compose](https://img.shields.io/badge/-Docker%20compose-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker Hub](https://img.shields.io/badge/-Docker%20Hub-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/products/docker-hub)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat&logo=GitHub%20actions&logoColor=56C0C0&color=008080)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat&logo=Yandex.Cloud&logoColor=56C0C0&color=008080)](https://cloud.yandex.ru/)

##Проект доступен по адресу 
```
http://51.250.104.38/recipes/
```

## Стек технологий
Python 3.9.7, Django 3.2.7, Django REST Framework 3.12, PostgresQL, Docker, Yandex.Cloud.

## Установка
Для запуска локально, создайте файл `.env` в директории `/backend/` с содержанием:
```
SECRET_KEY=любой_секретный_ключ_на_ваш_выбор
DEBUG=False
ALLOWED_HOSTS=*,или,ваши,хосты,через,запятые,без,пробелов
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=пароль_к_базе_данных_на_ваш_выбор
DB_HOST=bd
DB_PORT=5432
```

#### Установка Docker
Для запуска проекта вам потребуется установить Docker и docker-compose.

Для установки на ubuntu выполните следующие команды:
```bash
sudo apt install docker docker-compose
```

Про установку на других операционных системах вы можете прочитать в [документации](https://docs.docker.com/engine/install/) и [про установку docker-compose](https://docs.docker.com/compose/install/).

### Установка проекта на сервер
1. Скопируйте файлы из папки `/server/` на ваш сервер и `.env` файл из директории `/backend/`:
```bash
scp -r data/ <username>@<server_ip>:/home/<username>/
scp backend/.env <username>@<server_ip>:/home/<username>/
```
2. Зайдите на сервер и настройте `server_name` в конфиге nginx на ваше доменное имя:
```bash
vim nginx.conf
```
### Настройка проекта
1. Запустите docker compose:
```bash
docker-compose up -d
```
2. Примените миграции:
```bash
docker-compose exec backend python manage.py migrate
```
3. Заполните базу начальными данными (необязательно):
```bash
docker-compose exec backend python manange.py loaddata data/fixtures.json
```
4. Создайте суперюзера:
```bash
docker-compose exec backend python manage.py createsuperuser
```
5. Соберите статику:
```bash
docker-compose exec backend python manage.py collectstatic
```

## Как импортировать данные из своего csv файла?
Для начала убедитесь, что первая строчка вашего csv файла совпадает с названиями полей в модели. Если на первой строчке нет названия полей или они неправильные, исправьте, прежде чем приступать к импортированию.

## Документация к API
Чтобы открыть документацию локально, запустите сервер и перейдите по ссылке:
[http://127.0.0.1/api/docs/](http://127.0.0.1/api/docs/)
