from datetime import datetime

# -*- coding: utf-8 -*-

def normalize_date(date):
    '''Leads date to '%Y-%m-%d %H:%M' form (like 2019-01-10 09:41)
    if no time specified leads to '%Y-%m-%d' (2019-01-10)
    '''
    if 'вчера' in date or 'сегодня' in date:
        date = convert_relative_date_to_absolute(date)
        return str(datetime.strptime(date, '%d %m %Y %H:%M'))[:-3] # seconds removed
    date = replace_month_name_with_number(date)
    if ':' in date:
        return str(datetime.strptime(date, '%d %m %H:%M').replace(year=get_current_year()))[:-3]
    return str(datetime.strptime(date, '%d %m %Y').date())


def convert_relative_date_to_absolute(date):
    '''Converts date from 'Вчера 15:29' form to '10 1 2019 15:29' '''
    current_day = get_current_day()
    if 'вчера' in date:
        return replace_relative_day_with_absolute(date, 'вчера в', current_day - 1)
    return replace_relative_day_with_absolute(date, 'сегодня в', current_day)


def replace_month_name_with_number(date):
    months = {'января': '1', 'февраля': '2', 'марта': '3', 'апреля': '4', 'мая': '5', 'июня': '6',
              'июля': '7', 'августа': '8', 'сентября': '9', 'октября': '10', 'ноября': '11',
              'декабря': '12'}
    date_splitted = date.split()
    date_splitted[1] = months[date_splitted[1]]
    if 'в' in date:
        date_splitted.remove('в')
    return ' '.join(d for d in date_splitted)


def replace_relative_day_with_absolute(date, relative_day, absolute_day):
    return '{} {} {}'.format(absolute_day,
                             get_current_month(),
                             get_current_year()) + date.replace(relative_day, '')


def get_current_day():
    return datetime.today().day


def get_current_month():
    return '{:%m}'.format(datetime.now())


def get_current_year():
    return datetime.today().year