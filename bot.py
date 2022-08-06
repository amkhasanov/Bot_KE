import telebot, sqlite3
from telebot import types

TOKEN = '5542237999:AAG1Oy8z08aEHyieytR2cL2eu22fpZ8mCag'

DB = None
BOT = telebot.TeleBot(TOKEN)
ADMIN_ID = [927060137, 304440895]



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


@BOT.message_handler(commands=['menu'])
def menu(message):
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
    markup.add(btn1, btn2, btn3, btn4, btn5)
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
        # new_markup = types.InlineKeyboardMarkup(row_width=1)
        # btn_link1 = types.InlineKeyboardButton('MIRSEE - магазин солнечных очков', url='https://kazanexpress.ru/mirsee')
        # btn_link2 = types.InlineKeyboardButton('MIRSEE BIJOU - магазин бижутерии', url='https://kazanexpress.ru/mirsee-bijou')
        # btn_link3 = types.InlineKeyboardButton('AKVILONIA - фитнес резинки', url='https://kazanexpress.ru/akvilonia')
        # new_markup.add(btn_link1, btn_link2, btn_link3)
        # BOT.send_message(chat_id=message.chat.id,
        #                  text='👇🏻👇🏻👇🏻 Жми на кнопочки ниже и переходи в наши магазины, '
        #                       'чтобы увидеть весь ассортимент, подобранный специально для тебя😉\n\n'
        #                       'Или вернитесь в /menu .',
        #                  reply_markup=new_markup)
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
        BOT.register_next_step_handler(message, send_all)
        BOT.send_message(chat_id=message.chat.id,
                         text='Введите текст рассылки',
                         reply_markup=markup)
    else:
        BOT.send_message(chat_id=message.chat.id,
                         text='Я не понимаю Вас 🤷🏻‍♂️\n\n'
                              'Перейди в /menu чтобы выбрать действие.',
                         reply_markup=markup)


def main():
    global DB
    DB = sqlite3.connect('sqlite_bot.db', check_same_thread=False)
    cur = DB.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
       chat_id INT PRIMARY KEY,
       user_name TEXT);
    """)
    DB.commit()

    BOT.polling(none_stop=True)


def insert_chat(chat_id: int, user_name: str):
    cur = DB.cursor()
    cur.execute("""INSERT INTO chats(chat_id, user_name) 
       VALUES(?, ?);""", (chat_id, user_name))
    DB.commit()


if __name__ == "__main__":
    main()
