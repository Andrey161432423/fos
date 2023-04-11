# Цифровой фонд оценочных средств для кафедры ВУЗа

## Требования
- [Python 3.9.x](https://www.python.org/downloads/)
- [Git](https://git-scm.com)

## Деплой проекта

### 1. Склонировать репозиторий. 
```
git clone https://github.com/Andrey161432423/fos.git
```
### 2. Создание виртуальной среды.
Переходим в папку с проектом и выполняем команду:
```
python -m venv venv
```
Активируем виртуальную среду:
```
.\venv\Scripts\activate
```
Подгружаем зависимости проекта (пакеты):
```
pip install -r requirements.txt
```
### 3. Настройка проекта (миграции, статичные файлы).

Переходим в папку приложения.
```
cd project
```

Для настройки и заполнения базы данных с помощью миграций выполняем команды:
```
python manage.py makemigrations
python manage.py migrate
```

Генерируем статичные файлы:
```
python manage.py collectstatic
```

Создаем пользователя для админ-панели с помощью команды:
```
python manage.py createsuperuser
```

### 4. Запуск.

Запускаем веб-сервер Django через команду:
```
python manage.py runserver 80
```
_____
:white_check_mark: <b>Готово!</b> :+1: :tada: 

Проект запущен и доступен по адресу: `http://localhost/` или `http://127.0.0.1/`


