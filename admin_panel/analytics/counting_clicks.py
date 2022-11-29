def counting_button_clicks(queryset):
    clicks_count = {}
    for button in queryset:
        print(button, 'BUTTON!!!!')
        if button['button_title'] not in clicks_count.keys():
            clicks_count.setdefault(button['button_title'], 1)
        else:
            clicks_count[button['button_title']] += 1

    return clicks_count
