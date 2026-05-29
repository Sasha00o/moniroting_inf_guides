"""Управление Google Sheets: создание файлов, запись данных, форматирование."""

from datetime import date
from typing import List

from database.models import (
    InfoReason, Angle, Headline, Recommendation, Risk, UrgencyBoard, Report
)
from utils.helpers import report_filename, format_date_display, format_period_display
from utils.logger import sheets_logger


class SheetsManager:
    """Менеджер для работы с Google Sheets."""

    def __init__(self):
        """Инициализация клиента Google Sheets."""
        try:
            import gspread
            import os

            self.gspread = gspread
            self._client = None
            sheets_logger.info("SheetsManager инициализирован")
        except ImportError:
            sheets_logger.error("gspread не установлен")
            raise

    @property
    def client(self):
        """Lazy инициализация клиента с поддержкой OAuth и Service Account."""
        if self._client is None:
            from config import settings
            import os

            # Проверяем, какой метод авторизации использовать
            oauth_creds_path = getattr(
                settings, 'GOOGLE_OAUTH_CREDENTIALS', None)
            service_account_path = getattr(
                settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None)

            if oauth_creds_path and os.path.exists(oauth_creds_path):
                # OAuth 2.0 авторизация
                sheets_logger.info("Использую OAuth 2.0 авторизацию")
                self._client = self._authorize_oauth(oauth_creds_path)
            elif service_account_path and os.path.exists(service_account_path):
                # Service Account авторизация
                sheets_logger.info("Использую Service Account авторизацию")
                self._client = self.gspread.service_account(
                    filename=service_account_path)  # type: ignore
            else:
                raise ValueError(
                    "Не найдены credentials для Google Sheets. "
                    "Настройте GOOGLE_OAUTH_CREDENTIALS или GOOGLE_SERVICE_ACCOUNT_FILE"
                )

        return self._client

    def _authorize_oauth(self, credentials_path: str):
        """OAuth 2.0 авторизация для доступа от имени пользователя."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials as OAuthCredentials
        import os

        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]

        token_path = 'credentials/token.json'
        creds = None

        # Загружаем существующий токен
        if os.path.exists(token_path):
            try:
                creds = OAuthCredentials.from_authorized_user_file(
                    token_path, SCOPES)
                sheets_logger.info("Загружен существующий OAuth токен")
            except Exception as e:
                sheets_logger.warning(f"Не удалось загрузить токен: {e}")
                creds = None

        # Если токена нет или он истек
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    sheets_logger.info("Обновление OAuth токена...")
                    creds.refresh(Request())

                    # Сохраняем обновленный токен
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    sheets_logger.info("Токен успешно обновлен")
                except Exception as e:
                    sheets_logger.error(f"Не удалось обновить токен: {e}")
                    creds = None

            if not creds:
                # Токена нет - нужна первичная авторизация
                raise ValueError(
                    "OAuth токен не найден или истек. "
                    "Выполните первичную авторизацию:\n"
                    "1. На машине с браузером запустите: python authorize_oauth.py\n"
                    "2. Скопируйте созданный файл credentials/token.json на сервер"
                )

        # Используем метод authorize из gspread
        try:
            from gspread import auth
            return auth.authorize(creds)  # type: ignore
        except (ImportError, AttributeError):
            # Fallback для старых версий gspread
            import gspread as gspread_lib
            return gspread_lib.authorize(creds)  # type: ignore

    def create_report_file(self, geo: str, on_date: date | None = None) -> tuple[str, str]:
        """
        Создать новый файл Google Sheets для отчета.

        Args:
            geo: Код страны (BR, MX, etc.)
            on_date: Дата генерации (по умолчанию сегодня)

        Returns:
            (spreadsheet_id, file_url) - ID файла и ссылка для шаринга
        """
        from config import settings

        if on_date is None:
            on_date = date.today()

        filename = report_filename(geo, on_date)
        sheets_logger.info(f"Создаю новый файл Google Sheets: {filename}")

        try:
            # Создаем новый файл в указанной папке (если есть)
            if settings.GOOGLE_DRIVE_FOLDER_ID:
                # Создаем файл сразу в нужной папке
                spreadsheet = self.client.create(
                    filename, folder_id=settings.GOOGLE_DRIVE_FOLDER_ID)
            else:
                # Создаем в корне Drive Service Account
                spreadsheet = self.client.create(filename)

            spreadsheet_id = spreadsheet.id

            # Удаляем лист "Sheet1" (создается по умолчанию)
            try:
                spreadsheet.del_worksheet(spreadsheet.sheet1)
            except Exception:
                pass

            # Создаем лист "Отчет"
            worksheet = spreadsheet.add_worksheet("Отчет", rows=1000, cols=20)

            file_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            sheets_logger.info(f"Файл создан: {file_url}")

            return spreadsheet_id, file_url

        except Exception as e:
            sheets_logger.exception(f"Ошибка создания файла: {e}")
            raise

    def _prepare_header(self, geo: str, on_date: date, period_start: date, period_end: date, responsible: str | None, start_row: int):
        """Подготовка данных шапки для batch update."""
        from utils.helpers import format_geo_title

        geo_title = format_geo_title(geo)
        date_str = format_date_display(on_date)
        period_str = format_period_display(period_start, period_end)

        data = []
        data.append([f"{geo_title} | {date_str}"])
        data.append([f"Период: {period_str}"])
        if responsible:
            data.append([f"Ответственный: {responsible}"])
        else:
            data.append([""])
        # Ссылка на предыдущий выпуск (пока пусто, можно добавить логику поиска)
        data.append(["Предыдущий выпуск: —"])
        data.append([""])

        return data, start_row + 6

    def _prepare_block_0_feedback(self, start_row: int):
        """Подготовка блока обратной связи по прошлым выпускам."""
        data = []
        data.append(["📊 БЛОК 0: ОБРАТНАЯ СВЯЗЬ ПО ПРОШЛЫМ ВЫПУСКАМ"])
        data.append([""])
        data.append(["✅ Что зашло (высокая конверсия):"])
        data.append(["— Заполните вручную после анализа результатов"])
        data.append([""])
        data.append(["❌ Что не зашло (низкая конверсия):"])
        data.append(["— Заполните вручную после анализа результатов"])
        data.append([""])
        data.append(["💡 Выводы и рекомендации:"])
        data.append(["— Заполните вручную"])
        data.append([""])

        return data, start_row + len(data) + 1

    def _prepare_block_1_inforeasons(self, inforeasons: List[InfoReason], start_row: int):
        """Подготовка данных блока 1 для batch update."""
        data = []
        data.append(["📰 БЛОК 1: СЫРЫЕ ИНФОПОВОДЫ"])
        data.append(["Заголовок", "Источник", "Дата", "Категория",
                    "Описание", "Триггер", "Срочность"])

        for ir in inforeasons:
            urgency_display = "🔥 Срочно" if "24-48" in ir.urgency or "срочно" in ir.urgency.lower() else "⏳ " + \
                ir.urgency
            data.append([ir.title, ir.source_url, ir.date, ir.category,
                        ir.description, ir.emotional_trigger, urgency_display])

        data.append([""])
        return data, start_row + len(data) + 1

    def _prepare_block_2_angles(self, angles: List[Angle], start_row: int):
        """Подготовка данных блока 2 для batch update."""
        data = []
        data.append(["💡 БЛОК 2: УГЛЫ И ИДЕИ"])

        if not angles:
            data.append(["⚠️ Углы не созданы (проблема с AI генерацией)"])
            data.append([""])
            return data, start_row + len(data) + 1

        data.append(["ID", "Инфоповод", "Угол", "Связь с офером",
                    "Боль", "Тип", "Приоритет"])

        for angle in angles:
            data.append([str(angle.id), f"#{angle.inforeason_id}", angle.angle_text,
                        angle.offer_connection, angle.target_pain, angle.creative_type, angle.priority])

        data.append([""])
        return data, start_row + len(data) + 1

    def _prepare_block_3_headlines(self, headlines: List[Headline], start_row: int):
        """Подготовка данных блока 3 для batch update."""
        data = []
        data.append(["✍️ БЛОК 3: ЗАГОЛОВКИ"])

        if not headlines:
            data.append(["⚠️ Заголовки не созданы (нет углов)"])
            data.append([""])
            return data, start_row + len(data) + 1

        data.append(["Заголовок", "Идея #", "Формат", "Длина"])

        for headline in headlines:
            data.append([headline.text, str(headline.angle_id),
                        headline.format, str(headline.length)])

        data.append([""])
        return data, start_row + len(data) + 1

    def _prepare_block_4_recommendations(self, recommendations: List[Recommendation], start_row: int):
        """Подготовка данных блока 4 для batch update."""
        data = []
        data.append(["🎯 БЛОК 4: ТОП-5 РЕКОМЕНДАЦИЙ К ТЕСТУ"])

        if not recommendations:
            data.append(["⚠️ Рекомендации не созданы (недостаточно углов)"])
            data.append([""])
            return data, start_row + len(data) + 1

        data.append(["Ранг", "Идея #", "Обоснование", "Свежесть", "Триггер"])

        for rec in recommendations[:5]:
            data.append([f"#{rec.rank}", str(rec.angle_id), rec.reasoning[:100],
                        f"{rec.freshness_score}/10", f"{rec.trigger_strength_score}/10"])

        data.append([""])
        return data, start_row + len(data) + 1

    def _prepare_block_5_risks(self, risks: List[Risk], start_row: int):
        """Подготовка данных блока 5 для batch update."""
        data = []
        data.append(["⚠️ БЛОК 5: РИСКИ"])

        if not risks:
            data.append(["⚠️ Риски не оценены"])
            data.append([""])
            return data, start_row + len(data) + 1

        data.append(["Инфоповод #", "Юридический",
                    "Бан платформой", "Негатив аудитории", "Срок"])

        for risk in risks[:5]:
            data.append([str(risk.inforeason_id), risk.legal_risk[:30], risk.platform_ban_risk[:30],
                        risk.audience_backlash_risk[:30], risk.expiry_time[:30]])

        data.append([""])
        return data, start_row + len(data) + 1

    def _prepare_block_6_urgency(self, urgency_board: UrgencyBoard, start_row: int):
        """Подготовка данных блока 6 для batch update."""
        data = []
        data.append(["⏰ БЛОК 6: СРОЧНОСТЬ"])

        urgent_str = ", ".join(
            str(id) for id in urgency_board.urgent_48h) if urgency_board.urgent_48h else "—"
        data.append(["🔥 Срочно (24-48ч)", urgent_str])

        wait_str = ", ".join(
            str(id) for id in urgency_board.can_wait) if urgency_board.can_wait else "—"
        data.append(["⏳ Можно позже", wait_str])

        return data, start_row + len(data) + 1

    def write_report(self, report: Report) -> str:
        """
        Запись полного отчета в Google Sheets с batch updates.

        Returns:
            URL файла
        """
        from utils.helpers import news_period, format_date

        # Создаем файл
        spreadsheet_id, file_url = self.create_report_file(report.geo)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.sheet1

        # Вычисляем период
        period_start, period_end = news_period()

        # Собираем все данные в один массив для batch update
        all_data = []
        current_row = 1

        # Шапка
        header_data, current_row = self._prepare_header(
            report.geo, date.today(), period_start, period_end, report.responsible, current_row
        )
        all_data.extend(header_data)

        # Блок 0: Обратная связь
        block0_data, current_row = self._prepare_block_0_feedback(current_row)
        all_data.extend(block0_data)

        # Блок 1: Инфоповоды
        block1_data, current_row = self._prepare_block_1_inforeasons(
            report.inforeasons, current_row)
        all_data.extend(block1_data)

        # Блок 2: Углы
        block2_data, current_row = self._prepare_block_2_angles(
            report.angles, current_row)
        all_data.extend(block2_data)

        # Блок 3: Заголовки
        block3_data, current_row = self._prepare_block_3_headlines(
            report.headlines, current_row)
        all_data.extend(block3_data)

        # Блок 4: Рекомендации
        block4_data, current_row = self._prepare_block_4_recommendations(
            report.recommendations, current_row)
        all_data.extend(block4_data)

        # Блок 5: Риски
        block5_data, current_row = self._prepare_block_5_risks(
            report.risks, current_row)
        all_data.extend(block5_data)

        # Блок 6: Срочность
        if report.urgency_board:
            block6_data, current_row = self._prepare_block_6_urgency(
                report.urgency_board, current_row)
            all_data.extend(block6_data)

        # Batch update - один запрос вместо сотен
        sheets_logger.info(
            f"Запись {len(all_data)} строк в Google Sheets через batch update")
        if all_data:
            worksheet.batch_update([{'range': 'A1', 'values': all_data}])

        sheets_logger.info(f"Отчет записан в Google Sheets: {file_url}")
        return file_url
