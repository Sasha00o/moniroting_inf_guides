"""Скрипт для первичной OAuth авторизации на локальной машине."""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def authorize():
    """Выполнить OAuth авторизацию и сохранить токен."""
    credentials_path = 'credentials/oauth_credentials.json'
    token_path = 'credentials/token.json'

    if not os.path.exists(credentials_path):
        print(f"❌ Файл {credentials_path} не найден!")
        print("Скачайте OAuth credentials из Google Cloud Console")
        return

    print("🔐 Запуск OAuth авторизации...")
    print("Сейчас откроется браузер для авторизации")

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Сохраняем токен
    os.makedirs('credentials', exist_ok=True)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())

    print(f"✅ Авторизация успешна!")
    print(f"✅ Токен сохранен в {token_path}")
    print("\nТеперь скопируйте файл token.json на сервер в папку credentials/")

if __name__ == "__main__":
    authorize()
