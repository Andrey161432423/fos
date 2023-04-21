<table cellspacing="0" cellpadding="0" style="border:none">
<tr style="border: none">
<td style="border: none" width="75%"><h1>Цифровой фонд оценочных средств для кафедры ВУЗа</h1></td>
<td style="border: none"><img src="https://rsue.ru/bitrix/templates/info_light_blue/img/logo.svg" width="200" height="200" />
</td>
</tr>
</table>
<hr>

## Требования
- [Python 3.9.x](https://www.python.org/downloads/)
- [Git](https://git-scm.com)

## Установка проекта

> Выполняется **один раз** при первом развертывании проекта в заданной среде.

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
### 3. Настройка проекта (миграции, статичные файлы, тема).

Переходим в папку приложения.
```
cd project
```

Для настройки и заполнения базы данных с помощью миграций выполняем команды:
```
python manage.py makemigrations
python manage.py migrate
```

Импортируем настройки темы оформления:
```
python manage.py loaddata theme.json
```

Генерируем статичные файлы:
```
python manage.py collectstatic
```

Создаем пользователя для админ-панели с помощью команды:
```
python manage.py createsuperuser
```

Заполнение базы данных значениями по-умолчанию:
```
python manage.py seed
```

## Деплой проекта

> Выполняется **постоянно** при получении новых изменений

### 1. Виртуальная среда

Находясь в папке с проектом активируем виртуальную среду:
```
.\venv\Scripts\activate
```

Подгружаем зависимости проекта (пакеты):
```
pip install -r requirements.txt
```

### 2. Миграции и статика

Переходим в папку приложения.
```
cd project
```

Генерируем и применяем миграции:
```
python manage.py makemigrations
python manage.py migrate
```

Генерируем статичные файлы:
```
python manage.py collectstatic
```

### 3. Запуск.

Запускаем веб-сервер Django через команду:
```
python manage.py runserver 80
```
_____
:white_check_mark: <b>Готово!</b> :+1: :tada: 

Проект запущен и доступен по адресу: `http://localhost/` или `http://127.0.0.1/`


