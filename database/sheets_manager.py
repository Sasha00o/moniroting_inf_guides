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
            from google.oauth2.service_account import Credentials

            self.gspread = gspread
            self.Credentials = Credentials
            self._client = None
            sheets_logger.info("SheetsManager инициализирован")
        except ImportError:
            sheets_logger.error("gspread или google-auth не установлены")
            raise

    @property
    def client(self):
        """Lazy инициализация клиента."""
        if self._client is None:
            from config import settings

            creds = self.Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive']
            )
            self._client = self.gspread.authorize(creds)
        return self._client

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
            # Создаем новый файл
            spreadsheet = self.client.create(filename)
            spreadsheet_id = spreadsheet.id

            # Перемещаем в нужную папку если указана
            if settings.GOOGLE_DRIVE_FOLDER_ID:
                try:
                    self.client.drive.move_file(
                        spreadsheet_id,
                        settings.GOOGLE_DRIVE_FOLDER_ID
                    )
                except AttributeError:
                    sheets_logger.warning(
                        "gspread client has no drive.move_file; skipping move. Use Drive API to move file.")

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

    def write_header(
        self,
        worksheet,
        geo: str,
        on_date: date,
        period_start: date,
        period_end: date,
        responsible: str | None = None,
    ) -> int:
        """
        Запись шапки отчета (название, дата, период).

        Returns:
            Номер строки после шапки (для начала блоков)
        """
        from utils.helpers import format_geo_title

        geo_title = format_geo_title(geo)
        date_str = format_date_display(on_date)
        period_str = format_period_display(period_start, period_end)

        # Строка 1: Заголовок
        worksheet.update_cell(1, 1, f"{geo_title} | {date_str}")
        worksheet.merge_cells('A1:H1')

        # Строка 2: Период
        worksheet.update_cell(2, 1, f"Период: {period_str}")
        worksheet.merge_cells('A2:H2')

        if responsible:
            worksheet.update_cell(3, 1, f"Ответственный: {responsible}")

        # Форматирование шапки
        self._format_header(worksheet)

        return 5  # Начало блоков после шапки

    def write_block_1_inforeasons(
        self,
        worksheet,
        inforeasons: List[InfoReason],
        start_row: int,
    ) -> int:
        """Запись Блока 1: Сырые инфоповоды."""
        if not inforeasons:
            return start_row

        # Заголовок блока
        worksheet.update_cell(start_row, 1, "📰 БЛОК 1: СЫРЫЕ ИНФОПОВОДЫ")
        worksheet.merge_cells(f'A{start_row}:G{start_row}')
        self._format_block_header(worksheet, start_row)

        # Заголовки колонок
        headers = ["Заголовок", "Источник", "Дата",
                   "Категория", "Описание", "Триггер", "Срочность"]
        for col, header in enumerate(headers, 1):
            worksheet.update_cell(start_row + 1, col, header)

        # Данные
        for i, ir in enumerate(inforeasons):
            row = start_row + 2 + i
            worksheet.update_cell(row, 1, ir.title)
            worksheet.update_cell(row, 2, ir.source_url)  # Будет гиперссылка
            worksheet.update_cell(row, 3, ir.date)
            worksheet.update_cell(row, 4, ir.category)
            worksheet.update_cell(row, 5, ir.description)
            worksheet.update_cell(row, 6, ir.emotional_trigger)

            # Срочность с эмодзи
            urgency_display = "🔥 Срочно" if "24-48" in ir.urgency or "срочно" in ir.urgency.lower() else "⏳ " + \
                ir.urgency
            worksheet.update_cell(row, 7, urgency_display)

        return start_row + 2 + len(inforeasons) + 2

    def write_block_2_angles(
        self,
        worksheet,
        angles: List[Angle],
        start_row: int,
    ) -> int:
        """Запись Блока 2: Углы и идеи."""
        if not angles:
            return start_row

        # Заголовок блока
        worksheet.update_cell(start_row, 1, "💡 БЛОК 2: УГЛЫ И ИДЕИ")
        worksheet.merge_cells(f'A{start_row}:G{start_row}')
        self._format_block_header(worksheet, start_row)

        # Заголовки колонок
        headers = ["ID", "Инфоповод", "Угол",
                   "Связь с офером", "Боль", "Тип", "Приоритет"]
        for col, header in enumerate(headers, 1):
            worksheet.update_cell(start_row + 1, col, header)

        # Данные
        for i, angle in enumerate(angles):
            row = start_row + 2 + i
            worksheet.update_cell(row, 1, str(angle.id))
            worksheet.update_cell(row, 2, f"#{angle.inforeason_id}")
            worksheet.update_cell(row, 3, angle.angle_text)
            worksheet.update_cell(row, 4, angle.offer_connection)
            worksheet.update_cell(row, 5, angle.target_pain)
            worksheet.update_cell(row, 6, angle.creative_type)

            # Приоритет с цветом (для условного форматирования)
            worksheet.update_cell(row, 7, angle.priority)

        return start_row + 2 + len(angles) + 2

    def write_block_3_headlines(
        self,
        worksheet,
        headlines: List[Headline],
        start_row: int,
    ) -> int:
        """Запись Блока 3: Заголовки."""
        if not headlines:
            return start_row

        # Заголовок блока
        worksheet.update_cell(start_row, 1, "✍️ БЛОК 3: ЗАГОЛОВКИ")
        worksheet.merge_cells(f'A{start_row}:D{start_row}')
        self._format_block_header(worksheet, start_row)

        # Заголовки колонок
        headers = ["Заголовок", "Идея #", "Формат", "Длина"]
        for col, header in enumerate(headers, 1):
            worksheet.update_cell(start_row + 1, col, header)

        # Данные
        for i, headline in enumerate(headlines):
            row = start_row + 2 + i
            worksheet.update_cell(row, 1, headline.text)
            worksheet.update_cell(row, 2, str(headline.angle_id))
            worksheet.update_cell(row, 3, headline.format)
            worksheet.update_cell(row, 4, str(headline.length))

        return start_row + 2 + len(headlines) + 2

    def write_block_4_recommendations(
        self,
        worksheet,
        recommendations: List[Recommendation],
        start_row: int,
    ) -> int:
        """Запись Блока 4: Рекомендации для теста (топ-5)."""
        if not recommendations:
            return start_row

        # Заголовок блока
        worksheet.update_cell(
            start_row, 1, "🎯 БЛОК 4: ТОП-5 РЕКОМЕНДАЦИЙ К ТЕСТУ")
        worksheet.merge_cells(f'A{start_row}:E{start_row}')
        self._format_block_header(worksheet, start_row)

        # Заголовки колонок
        headers = ["Ранг", "Идея #", "Обоснование", "Свежесть", "Триггер"]
        for col, header in enumerate(headers, 1):
            worksheet.update_cell(start_row + 1, col, header)

        # Данные
        for i, rec in enumerate(recommendations[:5]):
            row = start_row + 2 + i
            worksheet.update_cell(row, 1, f"#{rec.rank}")
            worksheet.update_cell(row, 2, str(rec.angle_id))
            worksheet.update_cell(row, 3, rec.reasoning[:100])
            worksheet.update_cell(row, 4, f"{rec.freshness_score}/10")
            worksheet.update_cell(row, 5, f"{rec.trigger_strength_score}/10")

        return start_row + 2 + len(recommendations[:5]) + 2

    def write_block_5_risks(
        self,
        worksheet,
        risks: List[Risk],
        start_row: int,
    ) -> int:
        """Запись Блока 5: Риски."""
        if not risks:
            return start_row

        # Заголовок блока
        worksheet.update_cell(start_row, 1, "⚠️ БЛОК 5: РИСКИ")
        worksheet.merge_cells(f'A{start_row}:E{start_row}')
        self._format_block_header(worksheet, start_row)

        # Заголовки колонок
        headers = ["Инфоповод #", "Юридический",
                   "Бан платформой", "Негатив аудитории", "Срок"]
        for col, header in enumerate(headers, 1):
            worksheet.update_cell(start_row + 1, col, header)

        # Данные
        for i, risk in enumerate(risks[:5]):
            row = start_row + 2 + i
            worksheet.update_cell(row, 1, str(risk.inforeason_id))
            worksheet.update_cell(row, 2, risk.legal_risk[:30])
            worksheet.update_cell(row, 3, risk.platform_ban_risk[:30])
            worksheet.update_cell(row, 4, risk.audience_backlash_risk[:30])
            worksheet.update_cell(row, 5, risk.expiry_time[:30])

        return start_row + 2 + len(risks[:5]) + 2

    def write_block_6_urgency(
        self,
        worksheet,
        urgency_board: UrgencyBoard,
        start_row: int,
    ) -> int:
        """Запись Блока 6: Срочность."""
        # Заголовок блока
        worksheet.update_cell(start_row, 1, "⏰ БЛОК 6: СРОЧНОСТЬ")
        worksheet.merge_cells(f'A{start_row}:B{start_row}')
        self._format_block_header(worksheet, start_row)

        # Срочно 24-48ч
        worksheet.update_cell(start_row + 1, 1, "🔥 Срочно (24-48ч)")
        urgent_str = ", ".join(
            str(id) for id in urgency_board.urgent_48h) if urgency_board.urgent_48h else "—"
        worksheet.update_cell(start_row + 1, 2, urgent_str)

        # Можно позже
        worksheet.update_cell(start_row + 2, 1, "⏳ Можно позже")
        wait_str = ", ".join(
            str(id) for id in urgency_board.can_wait) if urgency_board.can_wait else "—"
        worksheet.update_cell(start_row + 2, 2, wait_str)

        return start_row + 4

    def _format_header(self, worksheet):
        """Форматирование шапки отчета."""
        try:
            # Синий фон для шапки
            light_blue = {
                "red": 0.2,
                "green": 0.6,
                "blue": 1.0
            }
            white_text = {
                "red": 1.0,
                "green": 1.0,
                "blue": 1.0
            }

            for row in range(1, 4):
                for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                    cell = worksheet.cell_value(row, ord(col) - ord('A') + 1)
                    if cell:  # Если есть текст
                        pass  # Форматирование через batch_update если нужно
        except Exception as e:
            sheets_logger.warning(f"Ошибка форматирования шапки: {e}")

    def _format_block_header(self, worksheet, row: int):
        """Форматирование заголовка блока."""
        try:
            # Серый фон для заголовков блоков
            pass  # Форматирование через batch_update если нужно
        except Exception as e:
            sheets_logger.warning(
                f"Ошибка форматирования заголовка блока: {e}")

    def write_report(self, report: Report) -> str:
        """
        Запись полного отчета в Google Sheets.

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

        # Пишем все блоки
        current_row = self.write_header(
            worksheet,
            report.geo,
            date.today(),
            period_start,
            period_end,
            report.responsible
        )

        current_row = self.write_block_1_inforeasons(
            worksheet, report.inforeasons, current_row)
        current_row = self.write_block_2_angles(
            worksheet, report.angles, current_row)
        current_row = self.write_block_3_headlines(
            worksheet, report.headlines, current_row)

        if report.recommendations:
            current_row = self.write_block_4_recommendations(
                worksheet, report.recommendations, current_row)

        if report.risks:
            current_row = self.write_block_5_risks(
                worksheet, report.risks, current_row)

        if report.urgency_board:
            current_row = self.write_block_6_urgency(
                worksheet, report.urgency_board, current_row)

        sheets_logger.info(f"Отчет записан в Google Sheets: {file_url}")
        return file_url
