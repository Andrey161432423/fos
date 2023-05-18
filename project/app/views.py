import xlsxwriter
from django.http import FileResponse, HttpResponse
from app.models import Document as DocModel, Fos, Discipline
from docxcompose.composer import Composer
from docx import Document
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from transliterate import translit
import os
from django.conf import settings
import traceback
from io import BytesIO
from django.contrib.auth.models import User


def export_fos(request):
    """
        Данный метод отвечает за реализацию функционала по экспорту (в excel) отчета ФОСов заданного преподавателя
    """

    # если преподаватель не выбран - возвращаем ошибку и делаем редирект обратно на страницу списка ФОСов
    if not 'teacher' in request.POST:
        messages.add_message(request, messages.ERROR, 'Не выбран преподаватель')
        return redirect('/admin/app/fos/')

    # получаем преподавателя и все его дисциплины
    teacher = User.objects.get(pk=request.POST['teacher'])
    disciplines = Discipline.objects.filter(users__in=request.POST['teacher'])

    # создаем объект для работы с записью в excel файл
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # инициализируем лист
    worksheet = workbook.add_worksheet()

    # добавляем заголовок
    worksheet.merge_range('A2:H2', 'Фонд оценочных средств', workbook.add_format({
        'bold': True, 'font_size': 14, 'align': 'left', 'valign': 'vcenter'
    }))

    # создаем стиль для заголовочной строки таблицы
    header = workbook.add_format({
        'bg_color': '#F7F7F7', 'bold': True, 'color': 'black', 'align': 'center', 'valign': 'vcenter','border': 1
    })

    # добавляем заголовочные строки таблицы
    worksheet.merge_range('A4:A5', 'Преподаватель', header)
    # формируем заголовок "дисциплины" (3 строка и объединяем столько колонок - сколько дисциплин)
    worksheet.merge_range(
        first_row=3, first_col=1, last_row=3, last_col=len(disciplines),
        data='Дисциплины', cell_format=header
    )
    worksheet.set_column(0, 0, 25)
    worksheet.set_column(1, len(disciplines), 15)

    style_default = workbook.add_format({'border': 1})
    style = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True
    })
    col = 1
    count_fos = []
    # перебираем все дисциплины
    for d in disciplines:
        # записываем название дисциплины в 4 строку в соответствующую колонку
        worksheet.write(4, col, d.name, header)
        # ширина такой ячейки - кол-во букв в дисциплине + 10
        worksheet.set_column(col, col, len(d.name) + 10)

        row = 5
        names = []
        count_fos.append(d.fos_set.count())
        # перебираем все ФОСы дисциплины
        for f in d.fos_set.all():
            fos = f.name + " (" + f.type.name + ")"
            names.append(fos)
            # начиная с 5 строки и соответствующей колонки записываем ФОС
            worksheet.write(row, col, fos, style_default)
            # переходим на след строку
            row += 1
        if len(names) > 0:
            # выставляем ширину колонки по максимально большому названию из ФОСов
            worksheet.set_column(col, col, len(max(names, key=len)))
        else:
            # если ФОСов в пределах дисциплины нет - пишем прочерк
            worksheet.write(row, col, '-', style)
        # переходим на следующую колонку
        col = col + 1

    # записываем имя преподавателя в 6 строку
    if teacher.first_name or teacher.last_name:
        username = teacher.first_name + " " + teacher.last_name
    else:
        username = teacher.username

    # делаем эту ячейку по ширине равной самому большому кол-ву строк ФОСов в дисциплинах
    if (5 + max(count_fos)) == 6:
        worksheet.write('A6:A6', username, style)
    else:
        worksheet.merge_range('A6:A' + str(5 + max(count_fos)), username, style)

    # далее необходимо найти пустые ячейки в каждой колонке (где ФОСов нет)
    # объединить их и поставить прочерк
    col = 1
    for d in disciplines:
        row = 5
        last_row = 0
        for f in range(0, max(count_fos)):
            # в пределах каждой колонки (дисциплины) ищем последнюю заполненную строчку
            try:
                d.fos_set.all()[f]
            except IndexError:
                # запоминаем индекс следующей пустой строки
                last_row = row
                break
            row += 1
        if last_row != 0:
            # в случае если есть пустые строки
            fr = last_row
            lw = max(count_fos) + 4

            if fr == lw:
                # если такая ячейка одна - ставим прочерк в ней
                worksheet.write(fr, col, '-', style)
            else:
                # если их несколько - объединяем все и ставим прочерк по центру
                worksheet.merge_range(
                    first_row=last_row, first_col=col, last_row=max(count_fos) + 4, last_col=col,
                    data='-', cell_format=style
                )
        col = col + 1

    # формируем стили для подписи "оценочные средства" справа от таблицы
    fos_text_style = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
    # разворачиваем текст
    fos_text_style.set_rotation(90)
    # добавляем перенос слов
    fos_text_style.set_text_wrap(True)
    # объединяем ячейки колонки {кол-во дисциплин+1} ОТ 5 строки + кол-во строк ФОСов
    # и пишем туда текст
    worksheet.merge_range(
        first_row=5, first_col=disciplines.count()+1, last_row=max(count_fos) + 4, last_col=disciplines.count() + 1,
        data='Оценочные средства', cell_format=fos_text_style
    )

    # далее формируем итоговую таблицу (где первый столбец - тип ФОСа, второй - их общее количество)
    # добавляем заголовок
    row = 7 + max(count_fos)
    worksheet.merge_range(
        first_row=row, first_col=0, last_row=row+2, last_col=1,
        data='Общее количество оценочных средств', cell_format=style
    )

    # формируем словарь, где элементы это типы ФОСов без повторений
    fos_types = dict()
    for d in disciplines:
        for f in d.fos_set.all():
            if f.type not in fos_types:
                f.type.total = 0
                fos_types[f.type.id] = f.type

    # считаем кол-во каждого типа ФОСов и общее кол-во
    all_total = 0
    for d in disciplines:
        for f in d.fos_set.all():
            fos_types[f.type.id].total += 1
            all_total += 1

    # перебираем все типы ФОСов
    row = 10 + max(count_fos)
    for ft in fos_types:
        # в первую колонку пишем название
        worksheet.write(row, 0, fos_types[ft].name, style)
        # во вторую - кол-во
        worksheet.write(row, 1, fos_types[ft].total, style)
        row += 1

    # добавляем строку где выводится общее кол-во всех ФОСОв
    total_format = workbook.add_format({
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'bold': True
    })
    worksheet.write(row, 0, 'Всего', total_format)
    # worksheet.write_formula(row, 1, '=SUM(B16:B'+str(row)+')', total_format)
    worksheet.write(row, 1, all_total, total_format)

    # создаем гистограмму
    chart = workbook.add_chart({'type': 'column'})

    # наименования - первый столбец (типы ФОСов)
    # значения - второй столбец (кол-во)
    chart.add_series({
        "categories": '=Sheet1!$A$'+str(11 + max(count_fos))+':$A$'+str(row),
        "values": '=Sheet1!$B$'+str(11 + max(count_fos))+':$B$'+str(row)
    })

    # добавляем заголовки и убираем легенду
    chart.set_title({"name": "Общее количество ОС"})
    chart.set_x_axis({"name": "Оценочные средства"})
    chart.set_y_axis({"name": "Кол-во"})
    chart.set_legend({'none': True})

    # вставляем гистограмму на лист
    worksheet.insert_chart(
        'A' + str(14 + max(count_fos) + len(fos_types)),
        chart, {'x_scale': 2, 'y_scale': 1}
    )

    # создаем и добавляем на лист круговую диаграмму
    chart_pie = workbook.add_chart({'type': 'pie'})
    chart_pie.add_series({
        "categories": '=Sheet1!$A$' + str(11 + max(count_fos)) + ':$A$' + str(row),
        "values": '=Sheet1!$B$' + str(11 + max(count_fos)) + ':$B$' + str(row),
        'data_labels': {'value': True},
    })
    chart_pie.set_title({"name": "Общее количество ОС"})
    worksheet.insert_chart(
        'A' + str(14 + max(count_fos) + len(fos_types) + 15),
        chart_pie, {'x_scale': 2, 'y_scale': 1}
    )

    # сохраняем excel документ
    workbook.close()

    # создаем объект ответа в формате excel
    response = HttpResponse(content_type='application/vnd.ms-excel')

    # указываем название файла
    response['Content-Disposition'] = 'attachment;filename="export.xlsx"'

    # добавляем сформированный excel файл в объект ответа и отдаем его на скачивание
    response.write(output.getvalue())
    return response


def merge_documents(request, fos_id):
    """
        Данный метод отвечает за реализацию функционала по объединению документов в пределах ФОСА
    """
    try:
        # находим требуемый ФОС и получаем его документы
        fos = get_object_or_404(Fos, pk=fos_id)
        documents = DocModel.objects.filter(fos_id=fos_id)

        # если у ФОСа не создано ни одного документа, или у первого из них нет физически загруженного файла
        if documents.count() < 1 or not documents[0].path:
            # возвращаем ошибку и делаем редирект на страницу ФОСа
            messages.add_message(request, messages.ERROR, 'Данный ФОС не содержит ни одного документа')
            return redirect(reverse('admin:app_fos_change', args=(fos_id,)))

        # если документ всего один - отдаем его на скачивание
        if documents.count() == 1:
            return FileResponse(
                open(documents[0].path.path, 'rb')
            )

        try:
            # добавляем в слияние первый документ
            master = Document(documents[0].path.path)
            composer = Composer(master)
        except Exception:
            # если первый из документов не является валидным MS Word файлом
            # возвращаем ошибку и делаем редирект на страницу ФОСа
            messages.add_message(request, messages.ERROR, 'Загруженный документ не является валидным MS Word файлом')
            return redirect(reverse('admin:app_fos_change', args=(fos_id,)))

        # перебираем все документы в ФОСе
        for doc in documents:
            # исключаем первый документ
            # проверяем что у каждого документа есть загруженный файл
            if doc.path and doc.id != documents[0].id:
                try:
                    new_doc = Document(doc.path.path)
                    composer.append(new_doc)
                except Exception:
                    # если какой-либо документ не является валидным MS Word файлом - пропускаем такой документ
                    pass

        # формируем название для объединенного файла (транслит названия дисциплины и ID ФОСа)
        merged_file_name = translit(fos.discipline.name, reversed=True) + "_fos_" + str(fos_id) + ".docx"
        # формируем путь для физического сохранения на диске и сохраняем файл
        pth = str(settings.BASE_DIR)
        merged_file_path = os.path.join(pth, "media", 'documents-merged', merged_file_name)
        composer.save('media/documents-merged/' + merged_file_name)

        # отдаем сохраненный файл на скачивание
        return FileResponse(
            open(merged_file_path, 'rb')
        )
    except Exception as e:
        # в случае возникновения ошибок - выводим их в консоль, а также возвращаем пользователю
        print(traceback.format_exc())
        messages.add_message(request, messages.ERROR, str(e))
        messages.add_message(request, messages.ERROR, 'Произошла непредвиденная ошибка. Попробуйте позже или '
                                                      'обратитесь к администратору')
        # и делаем редирект на страницу ФОСа
        return redirect(reverse('admin:app_fos_change', args=(fos_id,)))
