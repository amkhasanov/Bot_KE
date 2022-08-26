import logging
import sqlite3
from datetime import datetime, timezone, timedelta
import telebot
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
from telebot import types

from settings import TOKEN

DB = None
BOT = telebot.TeleBot(TOKEN)

def check_admin(message):
    cur = DB.cursor()
    cur.execute("""SELECT is_admin from chats WHERE chat_id=? 
                   """, (message.chat.id,))
    is_admin = cur.fetchone()
    return is_admin



def enter_date_step(message):
    try:
        last_date = datetime.strptime(message.text, "%d.%m.%Y %H:%M").replace(
            tzinfo=timezone(timedelta(hours=3))).timestamp()
        cur = DB.cursor()
        cur.execute("""UPDATE chats SET 
           last_send_date=?
           WHERE chat_id=?""", (last_date, message.chat.id))
        DB.commit()
        BOT.send_message(chat_id=message.chat.id,
                         text="Прикрепите картинку и добавтье подпись")
        BOT.register_next_step_handler(message, enter_img_txt_step)
    except ValueError:
        BOT.register_next_step_handler(message, enter_date_step)
        BOT.send_message(chat_id=message.chat.id,
                         text="Неверная дата. Введите дату в формате по МСК: 31.12.2022 22:00")


def enter_img_txt_step(message):
    cur = DB.cursor()
    cur.execute("""SELECT last_send_date from chats WHERE chat_id=? 
               """, (message.chat.id,))
    last_date = cur.fetchone()[0]

    if message.text == None:
        cur.execute("""INSERT INTO messages(message_id, message_text, message_photo) 
               VALUES(?, ?, ?);""", (message.message_id, message.caption, message.photo[-1].file_id))
    else:
        cur.execute("""INSERT INTO messages(message_id, message_text) 
                   VALUES(?, ?);""", (message.message_id, message.text,))

    DB.commit()
    scheduled_message(message, last_date)
    BOT.send_message(chat_id=message.chat.id,
                     text="Сообщение создано. Для возврата в основное меню - /menu")


def scheduled_message(message, last_date):
    date_scheduler = datetime.fromtimestamp(last_date)
    text = message.text
    caption = message.caption
    photo = message.photo[-1].file_id if text is None else None
    scheduler.add_job(sched, 'date', run_date=date_scheduler,
                      args=[text, caption, photo])
    logging.info(f"Задача добавлена в шедулер дата:{date_scheduler}")


def sched(text=None, caption=None, photo=None):
    logging.info(f"Выполнение запланированной задачи")
    cursor = DB.cursor()
    sqlite_select_query = """SELECT * from chats"""
    cursor.execute(sqlite_select_query)
    records = cursor.fetchall()
    if text:
        for user in records:
            send_all_message = text
            BOT.send_message(chat_id=user[0], text=send_all_message)
    else:
        for user in records:
            send_all_message = text
            BOT.send_photo(chat_id=user[0],
                           photo=photo, caption=caption)


def send_all(message):
    if check_admin(message)[0]:
        cursor = DB.cursor()
        sqlite_select_query = """SELECT * from chats"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()
        for user in records:
            send_all_message = message.text
            BOT.send_message(chat_id=user[0], text=send_all_message)
        BOT.send_message(chat_id=message.chat.id,
                         text="Рассылка отправлена. Нажми /menu чтобы вернуться в Основное меню")


@BOT.message_handler(commands=['start'])
def start(message):
    insert_chat(message.chat.id, message.from_user.username)
    bot_start_message = f'Спасибо за покупку, @{message.from_user.username} ! Мы приготовили для тебя несколько ' \
                        f'приятных подарков!\n\n' \
                        f'1️⃣ Возврат до 100 рублей за отзыв\n' \
                        f'2️⃣ Кэшбэк до 10% при покупках на KazanExpress\n' \
                        f'3️⃣ Доступ в  канал со скидками и акциями\n\n' \
                        f'🎁 🎁 🎁\n\n' \
                        f'Перейди в /menu и выбери свой подарок!'
    BOT.send_message(chat_id=message.chat.id, text=bot_start_message)


@BOT.message_handler(commands=['admin'])
def admin(message):
    if check_admin(message)[0]:
        print(check_admin(message)[0])
        bot_start_message = 'Введите ID-пользователя, которого необходимо добавить в "админы" \n' \
                            'Для удаления админа,введите ID-пользователя пробел удалить.\n' \
                            'Пример: 123456789 удалить  '
        BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
        BOT.register_next_step_handler(message, add_admin)
    else:
        bot_start_message = 'Вам не доступна данная команда. Для возврата в основное меню нажмите /menu '
        BOT.send_message(chat_id=message.chat.id, text=bot_start_message)


def add_admin(message):
    try:
        int(message.text)
    except ValueError:
        bot_start_message = 'Введен некорректный ID. Для возврата в основное меню нажмите /menu '
        BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
    admin_id_from_message = message.text.split()
    if len(admin_id_from_message) == 1:
        cur = DB.cursor()
        cur.execute("""SELECT * FROM chats WHERE chat_id=?;""", (message.text,))
        one_result = cur.fetchone()
        if one_result == None:
            bot_start_message = 'Такого пользователя нет в нашей базе.\n' \
                                'Необходимо чтобы он запустил команду "start"\n' \
                                'Для возврата в основное меню /menu'
            BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
        else:
            cur = DB.cursor()
            cur.execute("""UPDATE chats SET is_admin='1' WHERE chat_id=?;""", (int(message.text),))
            DB.commit()
            bot_start_message = 'Пользователь добавлен в список "админов".\n' \
                                'Для возврата в меню нажми /menu '
            BOT.send_message(chat_id=message.chat.id, text=bot_start_message)

    elif len(admin_id_from_message) == 2:
        cur = DB.cursor()
        cur.execute("""SELECT * FROM chats WHERE chat_id=?;""", (int(admin_id_from_message[0]),))
        one_result = cur.fetchone()
        if one_result == None:
            bot_start_message = 'Такого пользователя нет в нашей базе, либо введен неверный ID.\n' \
                               'Для возврата в основное меню /menu'
            BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
        else:
            cur = DB.cursor()
            cur.execute("""UPDATE chats SET is_admin='0' WHERE chat_id=?;""", (int(admin_id_from_message[0]),))
            DB.commit()
            bot_start_message = 'Пользователь удален из списка админов.\n' \
                                'Для возврата в меню нажми /menu '
            BOT.send_message(chat_id=message.chat.id, text=bot_start_message)


@BOT.message_handler(commands=['menu'])
def menu(message):
    insert_chat(message.chat.id, message.from_user.username)
    bot_menu_message = f'Для того, чтобы получить кэшбэк до 100%, нужно оставить максимально подробный отзыв с тремя ' \
                       f'фотографиями и прислать скриншот менеджеру в @mirsee \n' \
                       f'Чтобы получать постоянный кэшбэк от всех покупок до 10% нужно зарегистрироваться по ссылке ' \
                       f'ниже 👇🏻👇🏻👇🏻'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('🎁 Кэшбэк за отзыв до 100%')
    btn2 = types.KeyboardButton('💵 Кэшбэк от всех покупок 3-10%')
    btn3 = types.KeyboardButton('📲 Телеграм Константина')
    btn4 = types.KeyboardButton('💳 Наши магазины')
    markup.add(btn1, btn2, btn3, btn4)

    if check_admin(message)[0]:
        btn5 = types.KeyboardButton('Создать рассылку')
        markup.add(btn5)

    if check_admin(message)[0]:
        btn6 = types.KeyboardButton('Статистика')
        markup.add(btn6)
    BOT.register_next_step_handler(message, process_step)
    BOT.send_message(chat_id=message.chat.id, text=bot_menu_message, reply_markup=markup)

def process_step(message):
    markup = types.ReplyKeyboardRemove()
    if message.text == '💵 Кэшбэк от всех покупок 3-10%':
        BOT.send_message(chat_id=message.chat.id,
                         text='Совершай покупки выгодно!\n\n'
                              'Зарегистрируйся в сервисе Backit (EPN) и получай скидку от 3 до 10% на все товары '
                              'KazanExpress!\n\n'
                              'Ссылка для регистрации http://got.by/63vjex',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    elif message.text == '💳 Наши магазины':
        BOT.send_message(chat_id=message.chat.id,
                         text='Вступайте в нашу группу @kimmeriets чтобы получать ещё больше акционных товаров по '
                              'скидке. Так же там мы выкладываем эксклюзивную информацию о всём, что происходит за '
                              'кулисами нашей работы\n\n'
                              'В наших магазинах мы собрали ещё больше стильных аксессуаров, зацени!\n\n'
                              'https://kazanexpress.ru/mirsee - солнцезащитные и имиджевые очки. Самый большой выбор на '
                              'KazanExpress!\n\n'
                              'https://kazanexpress.ru/mirsee-bijou - потрясающая недорогая бижутерия. Стильные кольца, '
                              'цепочки, серёжки, чокеры и браслеты\n\n'
                              'https://kazanexpress.ru/akvilonia - фитнес товары, которые всегда можно взять с собой для'
                              ' поддержания лучшей формы!',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    elif message.text == '🎁 Кэшбэк за отзыв до 100%':
        BOT.send_message(chat_id=message.chat.id,
                         text='1. Напиши максимально подробный отзыв с 3 хорошими фотографиями товара в использовании.\n'
                              '2. Выложи отзыв и когда его опубликуют (примерно на следующий день), скинь скриншот с '
                              'отзывом и номером заказа менеджеру @mirsee.\n'
                              'Далее мы вернём Вам на карту полную стоимость товара, но не более 100 рублей.\n\n'
                              'Для возврата в меню нажми /menu',
                         reply_markup=markup)
    elif message.text == '📲 Телеграм Константина':
        BOT.send_message(chat_id=message.chat.id,
                         text='Вступай в личный телеграм канал основателя бренда.\n@kostolaz_live\n'
                              'Там всё просто и открыто о бизнесе и не только. \n\n'
                              'Для возврата в меню нажми /menu',
                         reply_markup=markup)
    elif message.text == 'Создать рассылку' and check_admin(message)[0]:
        BOT.register_next_step_handler(message, enter_date_step)
        BOT.send_message(chat_id=message.chat.id,
                         text='Введите дату и время. Введите дату в формате по МСК: 31.12.2022 22:00',
                         reply_markup=markup)
    elif message.text == 'Статистика' and check_admin(message)[0]:
        BOT.register_next_step_handler(message, analytics)
        cursor = DB.cursor()
        all_rows = cursor.execute("""SELECT count(*) from chats;""").fetchall()
        num_of_folowers = all_rows[0][0]

        BOT.send_message(chat_id=message.chat.id,
                         text=f'Количество подписчиков - {num_of_folowers}',
                         reply_markup=markup)
    else:
        BOT.send_message(chat_id=message.chat.id,
                         text='Я не понимаю Вас 🤷🏻‍♂️\n\n'
                              'Перейди в /menu чтобы выбрать действие.',
                         reply_markup=markup)

@BOT.message_handler(commands=['analytics'])
def analytics(message):
    bot_analytics_message = f'Выберите нужный вам период'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('За все время')
    btn2 = types.KeyboardButton('За месяц')
    btn3 = types.KeyboardButton('За неделю')
    markup.add(btn1, btn2, btn3)
    BOT.register_next_step_handler(message, analytics_button_step)
    BOT.send_message(chat_id=message.chat.id, text=bot_analytics_message, reply_markup=markup)


def analytics_button_step(message):
    markup = types.ReplyKeyboardRemove()
    if message.text == 'За все время':
        BOT.send_message(chat_id=message.chat.id,
                         text='количество подписчиков за все время и сколько из них читают',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    elif message.text == 'За месяц':
        BOT.send_message(chat_id=message.chat.id,
                         text='количество подписчиков за все месяй и сколько из них читают',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    elif message.text == 'За все неделю':
        BOT.send_message(chat_id=message.chat.id,
                         text='количество подписчиков за все неделю и сколько из них читают',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    else:
        BOT.send_message(chat_id=message.chat.id,
                         text='Я не понимаю Вас 🤷🏻‍♂️\n\n'
                              'Перейди в /menu чтобы выбрать действие.',
                         reply_markup=markup)


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    global DB
    DB = sqlite3.connect('sqlite_bot.db', check_same_thread=False)
    cur = DB.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
       chat_id INT PRIMARY KEY,
       user_name TEXT,
       last_send_date TIMESTAMP,
       is_admin BOOLEAN default 0 check (is_admin in (0,1)),
       subscription_date TIMESTAMP default (datetime('now', 'localtime')));
    """)
    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
           message_id INTEGER PRIMARY KEY,
           message_text TEXT,
           message_photo TEXT);
        """)
    DB.commit()

    global scheduler
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///sqlite_bot.db')
    }
    executors = {
        'default': ThreadPoolExecutor(20),
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
    scheduler.start()
    logging.info("Бот запущен!")
    BOT.polling(none_stop=True)


def insert_chat(chat_id: int, user_name: str):
    cur = DB.cursor()
    cur.execute("""SELECT chat_id from chats WHERE chat_id=?; """, (chat_id,))
    users = cur.fetchall()
    print(users)
    if not users:
        cur.execute("""INSERT INTO chats(chat_id, user_name) 
           VALUES(?, ?);""", (chat_id, user_name))
        DB.commit()


if __name__ == "__main__":
    main()
