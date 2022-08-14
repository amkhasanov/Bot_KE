import sqlite3
from datetime import datetime
import logging

import telebot
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc, timezone
from telebot import types
from tzlocal import get_localzone

TOKEN = '5542237999:AAG1Oy8z08aEHyieytR2cL2eu22fpZ8mCag'

DB = None
BOT = telebot.TeleBot(TOKEN)
ADMIN_ID = [927060137, 304440895]


def enter_date_step(message):
    try:
        last_date = datetime.strptime(message.text, "%d.%m.%Y %H:%M").timestamp()
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
    date_scheduler = datetime.fromtimestamp(last_date, tz=timezone('Europe/Moscow'))
    tz = get_localzone()  # local timezone
    text = message.text
    caption = message.caption
    photo = message.photo[-1].file_id if text is None else None
    scheduler.add_job(sched, 'date', run_date=date_scheduler, timezone=tz,
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
    if message.chat.id in ADMIN_ID:
        cursor = DB.cursor()
        sqlite_select_query = """SELECT * from chats"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()

        for user in records:
            send_all_message = message.text
            BOT.send_message(chat_id=user[0], text=send_all_message)
        BOT.send_message(chat_id=message.chat.id, text="Рассылка отправлена. Нажми /menu чтобы вернуться в Основное меню")


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


@BOT.message_handler(commands=['mailing'])
def mailing(message):
    bot_menu_message = f'Для того, чтобы получить кэшбэк до 100%, нужно оставить максимально подробный отзыв с тремя ' \
                       f'фотографиями и прислать скриншот менеджеру в @mirsee \n' \
                       f'Чтобы получать постоянный кэшбэк от всех покупок до 10% нужно зарегистрироваться по ссылке ' \
                       f'ниже 👇🏻👇🏻👇🏻'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('🎁 Кэшбэк за отзыв до 100%')
    btn2 = types.KeyboardButton('💵 Кэшбэк от всех покупок 3-10%')
    btn3 = types.KeyboardButton('📲 Канал с анонсами акций')
    btn4 = types.KeyboardButton('💳 Наши магазины')
    btn5 = types.KeyboardButton('Создать рассылку')
    btn6 = types.KeyboardButton('Список ваших рассылок')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    BOT.register_next_step_handler(message, process_step)
    BOT.send_message(chat_id=message.chat.id, text=bot_menu_message, reply_markup=markup)


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
    btn3 = types.KeyboardButton('📲 Канал с анонсами акций')
    btn4 = types.KeyboardButton('💳 Наши магазины')
    btn5 = types.KeyboardButton('Создать рассылку')
    btn6 = types.KeyboardButton('Список ваших рассылок')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
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
    elif message.text == '📲 Канал с анонсами акций':
        BOT.send_message(chat_id=message.chat.id,
                         text='Вступайте в нашу группу @kimmeriets чтобы получать ещё больше акционных товаров по '
                              'скидке. Так же там мы выкладываем эксклюзивную информацию о всём, что происходит за '
                              'кулисами нашей работы \n\n'
                              'Для возврата в меню нажми /menu',
                         reply_markup=markup)
    elif message.text == 'Создать рассылку':
        BOT.register_next_step_handler(message, enter_date_step)
        BOT.send_message(chat_id=message.chat.id,
                         text='Введите дату и время. В формате: 31.12.2022 22:00',
                         reply_markup=markup)
    elif message.text == 'Список ваших рассылок':
        cur = DB.cursor()
        cur.execute("""SELECT last_send_date from chats WHERE chat_id=? 
                       """, (message.chat.id,))
        last_date = cur.fetchone()[0]
        date_time = datetime.fromtimestamp(last_date)
        BOT.send_message(chat_id=message.chat.id,
                         text=
                         f'{i[0][:15]}..., дата отправки: {date_time}',
                         reply_markup=markup)

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
       last_send_date timestamp);
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
