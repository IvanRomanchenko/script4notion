from notion.block import CollectionViewBlock
from notion.client import NotionClient

from datetime import datetime
from dateutil.relativedelta import relativedelta
from re import search
import os


TOKEN_V2 = os.environ.get("TOKEN_V2")
URL_OF_TEST = os.environ.get("URL_OF_TEST")

client = NotionClient(token_v2=TOKEN_V2)
page = client.get_block(URL_OF_TEST)

# Забираем все задачи со статусом Done
rows = [i for j in [child.collection.get_rows() for child in page.children if isinstance(child, CollectionViewBlock)] for i in j if i.status == 'DONE' and i.periodicity not in (['On demand'], [])]

# Определяем сегодняшнюю дату
today = datetime.now().date()


def set_due_date(periodicity: list) -> datetime.date:
    """ Расчитывает дату для параметра <due_date> """

    periodicity = ''.join(periodicity)

    daily = search(r'Daily', periodicity)
    times_in = search(r'\dt\S*', periodicity)

    if daily:
        due_date = today + relativedelta(days=1)

    elif times_in:
        monday = 0 if search(r'Mo', periodicity) else None
        tuesday = 1 if search(r'Tue', periodicity) else None
        wednesday = 2 if search(r'Wed', periodicity) else None
        thursday = 3 if search(r'Thu', periodicity) else None
        friday = 4 if search(r'Fri', periodicity) else None

        weekday = monday or tuesday or wednesday or thursday or friday

        numb_of_times = int(times_in.group()[0])  # */N
        numb_of = times_in.group().split('/')[1]  # N/*

        if numb_of_times > 1:
            if numb_of[0].isdigit():
                if numb_of[1] == 'w':
                    days = int(numb_of[0])*7//numb_of_times
                elif numb_of[1] == 'm':
                    days = int(numb_of[0])*30//numb_of_times

            elif numb_of[0].isalpha():
                if numb_of[0] == 'w':
                    days = 7//numb_of_times
                elif numb_of[0] == 'm':
                    days = 30//numb_of_times

        elif numb_of_times == 1:
            if numb_of[0].isdigit():
                if numb_of[1] == 'w':
                    days = int(numb_of[0])*7//numb_of_times
                elif numb_of[1] == 'm':
                    days = int(numb_of[0])*30//numb_of_times

            elif numb_of[0].isalpha():
                if numb_of[0] == 'w':
                    days = 7//numb_of_times
                elif numb_of[0] == 'm':
                    days = 30//numb_of_times

        due_date = today + relativedelta(days=days, weekday=weekday)

    return due_date


# Расчитываем следующую дату на основе параметров в Periodicity property, ставим ее в due date
for row in rows:
    try:
        due_d = row.due_date.start

    except AttributeError:
        due_d = row.due_date

    finally:
        if due_d in (None, today):
            row.due_date = set_due_date(row.periodicity)

# Расчитываем дату, когда карточка должна быть перенесена в статус To Do.
for row in rows:
    try:
        set_d = row.set_date.start

    except AttributeError:
        set_d = row.set_date

    finally:
        if set_d is None or set_d < today:
            periodicity = ''.join(row.periodicity)
            due_d = row.due_date.start

            if search(r'Daily', periodicity):  # если Periodicity =  Daily, то set date = due date
                row.set_date = due_d

            elif search(r'/w', periodicity):  # если Periodicity =  */w, то set date = due date - 1 day
                row.set_date = due_d - relativedelta(days=1)

            elif search(r'/\dw', periodicity):  # если Periodicity =  */2w или */3w, то set date = due date - 3 day
                row.set_date = due_d - relativedelta(days=3)

            elif search(r'/m', periodicity):  # если Periodicity =  */m, то set date = due date - 1 week
                row.set_date = due_d - relativedelta(weeks=1)

            elif search(r'/\dm', periodicity):  # если Periodicity =  */2m или */3m, то set date = due date - 2 week
                row.set_date = due_d - relativedelta(weeks=2)

        elif row.set_date.start == today:  # если set date = today меняем Status property = To Do
            row.status = 'TO DO'
