#!/usr/bin/env python
"""
Script to download DejaVuSans font for PDF generation.
Run this script before starting the application.
"""
import os
import tempfile
import urllib.request
import zipfile


def download_dejavu_sans():
    """Загрузка шрифта DejaVuSans."""
    font_dir = 'fonts'
    font_path = os.path.join(font_dir, 'DejaVuSans.ttf')
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
    if not os.path.exists(font_path):
        print('Downloading DejaVuSans.ttf font...')
        # Используем альтернативный URL для загрузки шрифта
        url = 'https://dejavu-fonts.github.io/Files/dejavu-sans-ttf-2.37.zip'
        try:
            _download_and_extract_font(url, font_path)
            print(f'Font downloaded and extracted to {font_path}')
        except Exception as e:
            print(f"Ошибка при загрузке шрифта: {e}")
            _try_system_font(font_path)
    else:
        print(f'Font already exists at {font_path}')


def _download_and_extract_font(url, font_path):
    """Загружает и извлекает шрифт из архива."""
    # Создаем временный файл для загрузки архива
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
        urllib.request.urlretrieve(url, temp_file.name)

        # Распаковываем архив
        with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
            font_file_in_zip = _find_font_in_archive(zip_ref)
            if font_file_in_zip:
                _extract_font_file(zip_ref, font_file_in_zip, font_path)
            else:
                raise FileNotFoundError("Шрифт DejaVuSans.ttf не найден")
        # Удаляем временный файл
        os.unlink(temp_file.name)


def _find_font_in_archive(zip_ref):
    """Находит файл шрифта в архиве."""
    for file_name in zip_ref.namelist():
        if file_name.endswith('DejaVuSans.ttf'):
            return file_name
    return None


def _extract_font_file(zip_ref, font_file_in_zip, font_path):
    """Извлекает файл шрифта из архива."""
    with zip_ref.open(font_file_in_zip) as source_file, \
         open(font_path, 'wb') as target_file:
        target_file.write(source_file.read())


def _try_system_font(font_path):
    """Попытка использовать системный шрифт в случае ошибки загрузки."""
    system_font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if os.path.exists(system_font_path):
        import shutil
        shutil.copy(system_font_path, font_path)
        print(f'Used system font instead: {font_path}')


if __name__ == '__main__':
    download_dejavu_sans()
