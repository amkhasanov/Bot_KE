import sqlite3
from datetime import datetime, timezone, timedelta
from django.shortcuts import render
from admin_for_bot.settings import path_to_db
from analytics.counting_clicks import counting_button_clicks
from texts_for_bot.models import ButtonAnalytic

DB = sqlite3.connect(path_to_db, check_same_thread=False)
def show_admin_custom_page(request):
    cur = DB.cursor()
    planned_msgs = cur.execute("""SELECT * from texts_for_bot_plannedmessages WHERE 
    planned_date > datetime();""").fetchall()
    sended_msgs = cur.execute("""SELECT * from texts_for_bot_sendedmessages;""").fetchall()
    month = timedelta(days=30)
    week = timedelta(days=7)
    one_day = timedelta(days=1)
    per_month = datetime.now() - month
    per_week = datetime.now() - week
    per_day = datetime.now()
    end_date = datetime.now() + one_day
    clicks_per_all_time = ButtonAnalytic.objects.all().values()
    count_clicks_per_all_time = counting_button_clicks(clicks_per_all_time)
    clicks_button_per_month = clicks_per_all_time.filter(click_date__range=(per_month, end_date)).values()
    count_clicks_per_month = counting_button_clicks(clicks_button_per_month)
    clicks_button_per_week = clicks_per_all_time.filter(click_date__range=(per_week, end_date)).values()
    count_clicks_per_week = counting_button_clicks(clicks_button_per_week)
    clicks_button_per_day = clicks_per_all_time.filter(click_date__range=(per_day, end_date)).values()
    count_clicks_per_day = counting_button_clicks(clicks_button_per_day)
    clicks_count = {}
    for button_title in count_clicks_per_all_time.keys():
        count_per_day = count_clicks_per_day.get(button_title, 0)
        count_per_week = count_clicks_per_week.get(button_title, 0)
        count_per_month = count_clicks_per_month.get(button_title, 0)
        count_per_all_time = count_clicks_per_all_time.get(button_title, 0)
        clicks_count[button_title] = (count_per_day,
                                     count_per_week,
                                     count_per_month,
                                     count_per_all_time
                                     )
    data = {'planned_msgs': planned_msgs, 'sended_msgs': sended_msgs, 'clicks_count': clicks_count}
    return render(request, 'admin-custom-page.html', context=data)
