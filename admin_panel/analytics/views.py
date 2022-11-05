import sqlite3
from datetime import datetime, timezone, timedelta

from django.shortcuts import render
from admin_for_bot.settings import path_to_db

DB = sqlite3.connect(path_to_db, check_same_thread=False)


def show_admin_custom_page(request):
    cur = DB.cursor()
    planned_msgs = cur.execute("""SELECT * from texts_for_bot_plannedmessages WHERE 
    planned_date > datetime();""").fetchall()
    print('plnd msgs', planned_msgs)

    sended_msgs = cur.execute("""SELECT * from texts_for_bot_sendedmessages;""").fetchall()
    print('sended msgs', sended_msgs)
    data = {'planned_msgs': planned_msgs, 'sended_msgs': sended_msgs}
    return render(request, 'admin-custom-page.html', context=data)

