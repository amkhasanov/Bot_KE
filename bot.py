import logging
import sqlite3
from datetime import datetime, timezone, timedelta
import telebot
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
from telebot import types
from telebot.apihelper import ApiTelegramException

from settings import TOKEN, path_to_db

DB: sqlite3.Connection = None
BOT = telebot.TeleBot(TOKEN)


def is_admin(message) -> bool:
    cur = DB.cursor()
    cur.execute("""SELECT is_admin from chats WHERE chat_id=? 
                   """, (message.chat.id,))
    return cur.fetchone()[0]


def enter_date_step(message):
    if message.text == '/menu':
        menu(message)
    else:
        try:
            last_date = datetime.strptime(message.text, "%d.%m.%Y %H:%M").replace(
                tzinfo=timezone(timedelta(hours=3))).timestamp()
            cur = DB.cursor()
            cur.execute("""UPDATE chats SET 
               last_send_date=?
               WHERE chat_id=?;""", (last_date, message.chat.id))
            DB.commit()
            BOT.send_message(chat_id=message.chat.id,
                             text="Прикрепите картинку и добавтье подпись")
            BOT.register_next_step_handler(message, enter_img_txt_step)
        except ValueError:
            BOT.register_next_step_handler(message, enter_date_step)
            BOT.send_message(chat_id=message.chat.id,
                             text="Неверная дата. Введите дату в формате по МСК: 31.12.2022 22:00 \n"
                                  "'Перейти в /menu'")


def enter_img_txt_step(message):
    cur = DB.cursor()
    cur.execute("""SELECT last_send_date from chats WHERE chat_id=?; 
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

    cur = DB.cursor()
    if message.text == None:
        cur.execute("""INSERT INTO texts_for_bot_plannedmessages(planned_date, planned_msg_text) 
                  VALUES(?, ?);""", (date_scheduler, message.caption,))
    else:
        cur.execute("""INSERT INTO texts_for_bot_plannedmessages(planned_date, planned_msg_text)
                      VALUES(?, ?);""", (date_scheduler, message.text,))
    DB.commit()


def sched(text=None, caption=None, photo=None):
    logging.info(f"Выполнение запланированной задачи")
    cursor = DB.cursor()
    sqlite_select_query = """SELECT * from chats;"""
    cursor.execute(sqlite_select_query)
    records = cursor.fetchall()
    results = 0
    not_sended = 0
    if text:
        for user in records:
            try:
                sended = BOT.send_message(chat_id=user[0], text=text)
                results += 1 if sended else 0
            except ApiTelegramException:
                not_sended += 1

    else:
        for user in records:
            try:
                sended = BOT.send_photo(chat_id=user[0],
                           photo=photo, caption=caption)
                logging.info(f"sended {sended}")
                results += 1 if sended else 0
            except ApiTelegramException:
                not_sended += 1

    logging.info(f"scheduler send {results} messages, not send {not_sended}")

    dt_now = datetime.now()
    cur = DB.cursor()
    cur.execute("""INSERT INTO texts_for_bot_sendedmessages(send_date, not_send, success_send) 
                      VALUES(?, ?, ?);""", (dt_now, not_sended, results,))
    DB.commit()


@BOT.message_handler(commands=['start'])
def start(message):
    insert_chat(message.chat.id, message.from_user.username)
    cursor = DB.cursor()
    start_message_text = cursor.execute(
        """SELECT description from texts_for_bot_botmessage WHERE title = 'start_message';"""
    ).fetchone()
    bot_start_message = start_message_text[0]
    BOT.send_message(chat_id=message.chat.id, text=bot_start_message)


@BOT.message_handler(commands=['admin'])
def admin(message):
    if is_admin(message):
        bot_start_message = 'Введите ID-пользователя, которого необходимо добавить в "админы" \n' \
                            'Для удаления админа,введите ID-пользователя пробел удалить.\n' \
                            'Пример: 123456789 удалить  '
        BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
        BOT.register_next_step_handler(message, add_admin)
    else:
        bot_start_message = 'Вам не доступна данная команда. Для возврата в основное меню нажмите /menu '
        BOT.send_message(chat_id=message.chat.id, text=bot_start_message)


def add_admin(message):
    admin_id_from_message = message.text.split()
    if len(admin_id_from_message) == 1:
        try:
            int(admin_id_from_message[0])
        except ValueError:
            bot_start_message = 'Введен некорректный ID. Для возврата в основное меню нажмите /menu '
            BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
            return
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
        try:
            int(admin_id_from_message[0])
        except ValueError:
            bot_start_message = 'Введен некорректный ID. Для возврата в основное меню нажмите /menu '
            BOT.send_message(chat_id=message.chat.id, text=bot_start_message)
            return
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
    cursor = DB.cursor()
    bot_menu_message = "Что-то пошло не так. Напишите пожалуйста нашему менеджеру @mirsee и мы все исправим"
    menu_message_text = cursor.execute(
        """SELECT description from texts_for_bot_botmessage WHERE title = 'menu_message';"""
    ).fetchone()
    if menu_message_text:
        bot_menu_message = menu_message_text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cursor = DB.cursor()
    button_titles = cursor.execute(
        """SELECT title from texts_for_bot_buttontext;"""
    ).fetchall()
    for button in button_titles: #Создание кнопок
        title = button[0]
        if (title == 'Создать рассылку' or title == 'Статистика') and not is_admin(message):
            continue
        btn = types.KeyboardButton(title)
        markup.add(btn)
    BOT.register_next_step_handler(message, process_step)
    BOT.send_message(chat_id=message.chat.id, text=bot_menu_message, reply_markup=markup)


def process_step(message):
    button_title = message.text
    cursor = DB.cursor()
    button_id = cursor.execute(
        """SELECT id from texts_for_bot_buttontext 
        WHERE title = ?;""", (message.text,)).fetchall()[0][0]
    button_analytic(button_title, button_id)
    markup = types.ReplyKeyboardRemove()
    '''if check_admin(message)[0] == 0 and message.text == 'Создать рассылку':
        BOT.send_message(chat_id=message.chat.id,
                         text='Данная операция доступна только для админов \n'
                              'Перейти в /menu',
                         reply_markup=markup)'''

    cursor = DB.cursor()
    button_reply_message = cursor.execute(
        """SELECT message_after_click from texts_for_bot_buttontext WHERE title = ?;""",
        (message.text,)
    ).fetchone()

    if button_reply_message == ('Введите дату и время. Введите дату в формате по МСК:'
                          ' 31.12.2022 22:00\r\n\r\nПерейти в /menu',) and is_admin(message):
            BOT.register_next_step_handler(message, enter_date_step)
            BOT.send_message(chat_id=message.chat.id,
                             text=button_reply_message,
                             reply_markup=markup)
    elif button_reply_message == ('Выберите период',) and is_admin(message):
            analytics(message)
    elif button_reply_message:
        BOT.send_message(chat_id=message.chat.id,
                         text=button_reply_message,
                         reply_markup=markup)

    else:
        BOT.send_message(chat_id=message.chat.id,
                         text='Я не понимаю Вас 🤷🏻‍♂️\n\n'
                              'Перейди в /menu чтобы выбрать действие.',
                         reply_markup=markup)


def analytics(message):
    if is_admin(message):
        bot_analytics_message = f'Выберите нужный вам период'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn1 = types.KeyboardButton('За все время')
        btn2 = types.KeyboardButton('За месяц')
        btn3 = types.KeyboardButton('За неделю')
        markup.add(btn1, btn2, btn3)
        BOT.register_next_step_handler(message, analytics_button_step)
        BOT.send_message(chat_id=message.chat.id, text=bot_analytics_message, reply_markup=markup)
    else:
        bot_start_message = 'Вам не доступна данная команда. Для возврата в основное меню нажмите /menu '
        BOT.send_message(chat_id=message.chat.id, text=bot_start_message)


def analytics_button_step(message):
    markup = types.ReplyKeyboardRemove()
    if message.text == 'За все время':
        cursor = DB.cursor()
        all_subscribers = cursor.execute("""SELECT count(*) from chats;""").fetchall()
        num_of_subscribers = all_subscribers[0][0]
        BOT.send_message(chat_id=message.chat.id,
                         text=f'Количество подписчиков - {num_of_subscribers}.',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    elif message.text == 'За месяц':
        cursor = DB.cursor()
        month_subscribers = cursor.execute(
            """SELECT count(*) from chats WHERE subscription_date >= date('now', '-30 day');"""
        ).fetchall()
        num_of_month_subscribers = month_subscribers[0][0]

        BOT.send_message(chat_id=message.chat.id,
                         text=f'количество подписчиков за месяц {num_of_month_subscribers}.',
                         reply_markup=markup)
        BOT.send_message(chat_id=message.chat.id,
                         text='Для возврата в меню нажми /menu')
    elif message.text == 'За неделю':
        cursor = DB.cursor()
        week_subscribers = cursor.execute(
            """SELECT count(*) from chats WHERE subscription_date >= date('now', '-7 day');"""
        ).fetchall()
        num_of_week_subscribers = week_subscribers[0][0]
        BOT.send_message(chat_id=message.chat.id,
                         text=f'Количество подписчиков за неделю {num_of_week_subscribers}.',
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
    DB = sqlite3.connect(path_to_db, check_same_thread=False)
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
        'default': SQLAlchemyJobStore(url=f'sqlite:///{path_to_db}')
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
    if not users:
        cur.execute("""INSERT INTO chats(chat_id, user_name) 
           VALUES(?, ?);""", (chat_id, user_name))
        DB.commit()


def button_analytic(button_title, button_id):
    click_date = datetime.now()
    cur = DB.cursor()
    cur.execute("""INSERT INTO texts_for_bot_buttonanalytic(button_id, button_title, click_date)
    VALUES(?, ?, ?);""", (button_id, button_title, click_date))
    DB.commit()


if __name__ == "__main__":
    main()
