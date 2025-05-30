import csv
import json
import os
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для импорта ингредиентов из CSV или JSON файла."""
    help = 'Импортирует ингредиенты из CSV или JSON файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_extension = os.path.splitext(file_path)[1].lower()
        try:
            if file_extension == '.csv':
                self.import_from_csv(file_path)
            elif file_extension == '.json':
                self.import_from_json(file_path)
            else:
                raise CommandError(
                    'Неподдерживаемый формат файла. '
                    'Поддерживаются только CSV и JSON.'
                )
        except Exception as e:
            raise CommandError(
                f'Ошибка при импорте ингредиентов: {e}'
            )

        self.stdout.write(
            self.style.SUCCESS('Ингредиенты успешно импортированы')
        )

    def import_from_csv(self, file_path):
        """Импортирует ингредиенты из CSV файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                ingredients = []
                for row in reader:
                    name, measurement_unit = row
                    ingredients.append(
                        Ingredient(name=name,
                                   measurement_unit=measurement_unit)
                    )
                Ingredient.objects.bulk_create(
                    ingredients, ignore_conflicts=True
                )
        except FileNotFoundError:
            raise CommandError(f'Файл {file_path} не найден')
        except ValueError:
            raise CommandError(
                'Неверный формат CSV файла. '
                'Ожидаются колонки: название, единица измерения'
            )

    def import_from_json(self, file_path):
        """Импортирует ингредиенты из JSON файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                ingredients = []
                for item in data:
                    name = item.get('name')
                    measurement_unit = item.get('measurement_unit')
                    if not name or not measurement_unit:
                        raise ValueError(
                            'В JSON файле отсутствуют обязательные поля'
                        )
                    ingredients.append(
                        Ingredient(name=name,
                                   measurement_unit=measurement_unit)
                    )
                Ingredient.objects.bulk_create(
                    ingredients, ignore_conflicts=True
                )
        except FileNotFoundError:
            raise CommandError(f'Файл {file_path} не найден')
        except json.JSONDecodeError:
            raise CommandError('Неверный формат JSON файла')
