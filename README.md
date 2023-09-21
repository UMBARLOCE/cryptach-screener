# Cryptocurrency screener
Автоматический скринер криптовалют

## Инструкция по деплою
Данная инструкция предназначена для деплоя на Linux Ubuntu 20.04. Скринер можно разворачить на других ОС, но может потребоваться отступить от данной инструкции. 

1. Подготовьте сервер с Ubuntu 20.04. Можете воспользоваться [инструкцией от DigitalOcean](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-20-04-ru)https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-20-04-ru.
2. Установите зависимости:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   sudo apt-get install git docker docker-compose 
   ```
3. Перенесите файлы на сервер. Предлагается два способа, с помощью Git и прямая передача файлов на сервер с помощью SCP:

   3.1. Git (вам также потребуется токен Github. [Инструкция по его созданию](https://netology-code.github.io/guides/github-access-token/)https://netology-code.github.io/guides/github-access-token/)
   ```bash
   git clone https://github.com/khanbekov/cryptach-screener.git
   ```

   3.2. SCP (команду нужно выполнять на вашем компьютере, [полная инструкция по использованию SCP](https://help.reg.ru/support/servery-vps/oblachnyye-servery/rabota-s-serverom/kopirovaniye-faylov-cherez-ssh)):
   ```shell
   scp -r [путь к директории с исходным кодом] [директория на сервере]
   ```
   Пример:
   ```shell
   scp -r /home/screener/ root@123.123.123.123:/directory
   ```
4. Настройка скринера. Скопируйте файл `.env.dist` с новым именем `.env`:
   ```bash
   cp .env.dist .env
   ```
   Откройте файл `.env` c помощью текстового редактора (nano, vim или другой), замените значения переменных ADMINS (telegram id администраторов бота), BOT_TOKEN (токен телеграм бота от BotFather), CHANNEL_ID (id telegram канала, у бота должны быть права администратора в нем (для публикации сигналов)) на ваши.
6. Перейдите в директорию и соберите контейнер с помощью docker-compose:
   ```shell
   cd screener
   sudo docker-compose up
   ```
   
