from django.http import FileResponse
from app.models import Document as DocModel, Fos
from docxcompose.composer import Composer
from docx import Document
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from transliterate import translit
import os
from django.conf import settings
import traceback


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
        composer.save('media/documents-merged/'+merged_file_name)

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
