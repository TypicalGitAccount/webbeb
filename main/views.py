import base64
import io
import urllib.parse
import numpy as np
from django.shortcuts import render, render, redirect
from main.forms import Uploadfileform
import main.DataRecovery
from sqlite3 import connect
from re import match
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
from windrose import WindroseAxes
from django.http import HttpResponse
from PIL import Image
from os import listdir
from os.path import dirname, abspath
from io import BytesIO
from fpdf import FPDF
import tempfile


def error(request, err_msg, url):
    return render(request, 'exception.html', {'err_msg':err_msg})


def index(request):
    return render(request, "main.html")


def folder(request):
    exel_path = "/exel"
    path = dirname(abspath(__file__)) + exel_path
    img_list = listdir(path)
    return render(request, 'download.html', {'images': img_list})


def download(request, filename):
    exel_path = '/exel/'
    file_path = dirname(abspath(__file__)) + exel_path + filename
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


def download_report(request):
    file_path = '/home/laminat/Documents/code/web/webbeb/report.pdf'
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=report.pdf'
        return response


def upload(request):
    if request.method == 'POST':
        form = Uploadfileform(request.POST, request.FILES)
        for filename, file in request.FILES.items():
            if not match('^([а-яА-ЯіІґҐєЄїЇ]+)(\-)(20)[0-2][0-9](\-)\d+(.xlsx)$', str(file)):
                return redirect('/upload/error/'+'Назва файлу не відповідає формату : \'Місто-рік-місяць.xlsx\'')
            connection = connect(database='db.sqlite3')
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM main_uploadfolder')
            files = cursor.fetchall()
            for record in files:
                if 'main/exel/' + str(file) in record[0]:
                    return redirect('/upload/error/'+'Такий файл вже було завантажено! Оберіть, будь ласка, інший.')
            cursor.execute(f'INSERT INTO unrecovered (filename) VALUES (\'{file}\')')
            connection.commit()
            connection.close()
        if form.is_valid():
            form.save()
            connection = connect(database='db.sqlite3')
            cursor = connection.cursor()
            cursor.execute('UPDATE constants SET data_recovered = 0')
            connection.commit()
            connection.close()
            return redirect('/upload')
    else:
        form = Uploadfileform()
        return render(request, 'upload.html', {'form': form})


def recover(request):
    connection = connect(database='db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('SELECT data_recovered FROM constants')
    data_recovered = cursor.fetchall()[0][0]
    connection.close()
    if data_recovered == 1:
        return redirect('/recovered')
    return render(request, "recover.html")


def recover_ajax(request):
    connection = connect(database='db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('UPDATE constants SET data_recovered = 1')
    connection.commit()
    connection.close()
    path = dirname(abspath(__file__)) + '/exel/'
    main.DataRecovery.DataRecovery.recover_files(path, 'db.sqlite3')
    return HttpResponse(200)


def recovered(request):
    return render(request, "recovered.html")


def direction_to_float(direction):
    if direction == 'Північний':
        return 90
    if direction == 'Південний':
        return 270
    if direction == 'Західний':
        return 1
    if direction == 'Східний':
        return 180
    if direction == 'Південно-західний':
        return 315
    if direction == 'Північно-західний':
        return 45
    if direction == 'Північно-східний':
        return 145
    if direction == 'Південно-східний':
        return 225


def report(request):
    return render(request, 'report.html')


def reported(request, city, start_day, start_month, start_year, end_day, end_month, end_year):
    if (start_month > end_month and start_year >= end_year) or start_year > end_year:
        return redirect('/report/error/'+'Неправильно вказано дати!')

    if end_year - start_year > 1:
        return redirect('/report/error/'+'Максимальний період часу для звіту - 1 рік!')

    conn = connect(database='db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT day, time, month, year, temp, wind_speed, wind_direction FROM weather WHERE city == \'{city}\' AND year >= {start_year} AND year <= {end_year} ' +
        f'AND month >= {start_month} AND month <= {end_month}')
    db_data = cursor.fetchall()

    if not db_data:
        return redirect('/report/error/' + 'Дані за вказанимим регіоном і датами відстуні!')

    for line in db_data:
        if (line[2] == start_month and line[0] < start_day) or (line[2] == end_month and line[0] > end_day):
            db_data.remove(line)

    dates = [datetime(year=int(line[3]), month=line[2], day=line[0], hour=int(line[1][0:1]), minute=int(line[1][3:4]))
             for line in db_data]
    dates.sort()
    temps = [line[4] for line in db_data]
    conn.close()
    # temp chart
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=15))
    plt.xticks(rotation=90)
    plt.xlabel("Дата і час з інтервалом 15 діб")
    plt.ylabel("°С", rotation=0)
    plt.title('Температурні умови регіону')
    plt.tight_layout()
    plt.plot(dates, temps, label='bebra scheme')

    figure = plt.gcf()
    buff = io.BytesIO()
    figure.savefig(buff, format='png')
    buff.seek(0)
    str64 = base64.b64encode(buff.read())
    image = Image.open(BytesIO(base64.b64decode(str64)))
    temp_image = image.convert('RGB')
    image.close()
    temp_graph = urllib.parse.quote(str64)
    plt.close(figure)

    # # windrose

    wind_directions = []
    wind_speed = []
    for line in db_data:
        speed = line[5]
        if speed != 0:
            direction = direction_to_float(line[6])
            wind_directions.append(direction)
            wind_speed.append(speed)

    wind_speed = np.array(wind_speed, dtype=float)
    wind_directions = np.array(wind_directions, dtype=float)
    ax = WindroseAxes.from_ax()
    ax.bar(wind_directions, wind_speed, normed=True, opening=0.8, edgecolor='white')
    ax.set_xticklabels(['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE'])
    ax.set_theta_zero_location('N')
    ax.set_legend()
    plt.title('Роза вітрів регіону')
    figure = plt.gcf()
    buff = io.BytesIO()
    figure.savefig(buff, format='png')
    buff.seek(0)
    str64 = base64.b64encode(buff.read())
    image = Image.open(BytesIO(base64.b64decode(str64)))
    wind_rose_image = image.convert('RGB')
    image.close()
    wind_rose = urllib.parse.quote(str64)
    plt.close(figure)

    # temp duration chart
    temps_and_hours = {}
    for temp in temps:
        try:
            temps_and_hours[temp] += 0.5
        except:
            temps_and_hours[temp] = 0.5

    plt.bar(temps_and_hours.keys(), temps_and_hours.values(), align='center', alpha=0.5)
    plt.xlabel('T, °С')
    plt.ylabel('t, год', rotation=0)
    plt.title('Тривалість температурних режимів регіону')
    figure = plt.gcf()
    buff = io.BytesIO()
    figure.savefig(buff, format='png')
    buff.seek(0)
    str64 = base64.b64encode(buff.read())
    image = Image.open(BytesIO(base64.b64decode(str64)))
    temp_duration_image = image.convert('RGB')
    image.close()
    temp_duration_chart = urllib.parse.quote(str64)
    plt.close(figure)

    # wind speed duration chart
    wind_speed_and_hours = {}
    for line in db_data:
        wind_speed = line[5]
        try:
            wind_speed_and_hours[wind_speed] += 0.5
        except:
            wind_speed_and_hours[wind_speed] = 0.5

    plt.bar(wind_speed_and_hours.keys(), wind_speed_and_hours.values(), align='center', alpha=0.5)
    plt.xlabel('V, м/с')
    plt.ylabel('t, год', rotation=0)
    plt.title('Тривалість режимів вітрової активності регіону')
    figure = plt.gcf()
    buff = io.BytesIO()
    figure.savefig(buff, format='png')
    buff.seek(0)
    str64 = base64.b64encode(buff.read())
    image = Image.open(BytesIO(base64.b64decode(str64)))
    wind_duration_image = image.convert('RGB')
    image.close()
    wind_duration_chart = urllib.parse.quote(str64)
    plt.close(figure)

    bebra = {}
    for line in db_data:
        direction = line[6]
        try:
            bebra[direction] += 1
        except:
            bebra[direction] = 1

    hours = len(db_data) * 0.5
    still_hours = wind_speed_and_hours[0]
    unsteady_hours = bebra['Змінний']
    still_percentage = round(still_hours * 100 / hours)
    unsteady_percentage = round(unsteady_hours * 100 / hours)
    additional_winds = 'Штилі ≈ ' + str(still_percentage) + '%\nЗмінні ≈ ' + str(unsteady_percentage) + '%'

    # pdf report creation
    pdf = FPDF()
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)
    with tempfile.NamedTemporaryFile(mode="wb", suffix='.png') as png:
        temp_image.save(png.name)
        temp_image = temp_image.resize((600, 400))
        pdf.add_page(orientation='L')
        message = f'Звіт погодних умов регіону {city} за період з {start_day}.{start_month}.{start_year} по {end_day}.{end_month}.{end_year}'
        message = message.encode().decode('utf-8')
        pdf.write(h=1, txt=message)
        pdf.image(x=0, y=15, name=png.name)
    with tempfile.NamedTemporaryFile(mode="wb", suffix='.png') as png:
        temp_duration_image.save(png.name)
        pdf.add_page(orientation='L')
        pdf.image(png.name)
    with tempfile.NamedTemporaryFile(mode="wb", suffix='.png') as png:
        wind_duration_image.save(png.name)
        pdf.add_page(orientation='L')
        pdf.image(png.name)
    with tempfile.NamedTemporaryFile(mode="wb", suffix='.png') as png:
        wind_rose_image = wind_rose_image.resize((550, 550))
        wind_rose_image.save(png.name)
        abobka = f'Відсоток штилів ≈ {still_percentage}. Відстоток змінних вітрів ≈ {unsteady_percentage}'
        pdf.write(h=13, txt=abobka)
        pdf.image(x=0, y=20, name=png.name)


    pdf.output('report.pdf')
    pdf.close()

    return render(request, "reported.html",
                  {'data': [temp_graph, temp_duration_chart, wind_duration_chart], 'wind_rose': [wind_rose],
                   'additional_winds': additional_winds, 'report_label':message})
