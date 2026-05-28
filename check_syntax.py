"""Проверка синтаксиса всех новых файлов."""

import ast
import sys

files = [
    'bot/handlers.py',
    'bot/keyboards.py', 
    'bot/middlewares.py',
    'core/report_generator.py',
    'core/scheduler.py',
    'database/sheets_manager.py',
    'main.py'
]

errors = []
for fname in files:
    try:
        with open(fname, encoding='utf-8') as f:
            ast.parse(f.read())
        print(f'✅ {fname}')
    except SyntaxError as e:
        print(f'❌ {fname}: {e}')
        errors.append((fname, str(e)))
    except FileNotFoundError as e:
        print(f'⚠️  {fname}: Файл не найден')

if errors:
    print(f'\n❌ {len(errors)} файлов с ошибками')
    for fname, err in errors:
        print(f"  {fname}: {err}")
    sys.exit(1)
else:
    print('\n✅ Все файлы синтаксически корректны!')
    sys.exit(0)
