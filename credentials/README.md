# Google Service Account

1. Создайте Service Account в [Google Cloud Console](https://console.cloud.google.com).
2. Включите **Google Sheets API** и **Google Drive API**.
3. Скачайте JSON-ключ и сохраните как `google_service_account.json` в эту папку.
4. Создайте папку в Google Drive для отчётов и расшарьте её на email service account (роль **Editor**).
5. ID папки из URL добавьте в `.env` как `GOOGLE_DRIVE_FOLDER_ID`.

Файл `google_service_account.json` не коммитится в git (см. `.gitignore`).
