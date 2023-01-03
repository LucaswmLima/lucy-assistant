
import psycopg2
import num2words
import datetime

import pathlib
desktop = pathlib.Path.home() / 'Desktop'
print(desktop)

monthList = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
currentDate = (datetime.datetime.now()).strftime("%d/%m/%y")
day, month, year = currentDate.split('/')
currentDate = 'Hoje é %s de %s de 2000 e %s' % (
    num2words.num2words(day, lang='pt_BR'), monthList[int(month)-1], num2words.num2words(year, lang='pt_BR'))
print(currentDate)

