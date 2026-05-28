"""Планировщик задач через APScheduler."""

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from utils.logger import scheduler_logger


class ReportScheduler:
    """Планировщик для автоматической генерации отчетов."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Запуск планировщика с расписанием из конфига."""
        if self.is_running:
            return
        
        try:
            # Парсим CRON строку
            # Формат: "minute hour day month day_of_week"
            # Пример: "0 9 */3 * *" = каждые 3 дня в 9:00
            cron_parts = settings.SCHEDULE_CRON.split()
            
            if len(cron_parts) != 5:
                scheduler_logger.error(
                    f"Неверный формат CRON: {settings.SCHEDULE_CRON}. "
                    f"Ожидается: 'minute hour day month day_of_week'"
                )
                return
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # Импортируем обработчик в самом методе чтобы избежать циклических импортов
            from bot.handlers import scheduled_generate_all_geos
            
            self.scheduler.add_job(
                scheduled_generate_all_geos,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                ),
                name="scheduled_report_generation",
                misfire_grace_time=900,  # 15 минут для срабатывания если бот был оффлайн
            )
            
            scheduler_logger.info(
                f"Планировщик запущен. Расписание: {settings.SCHEDULE_CRON}"
            )
            
            self.scheduler.start()
            self.is_running = True
            
        except Exception as e:
            scheduler_logger.exception(f"Ошибка запуска планировщика: {e}")

    def stop(self):
        """Остановка планировщика."""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            scheduler_logger.info("Планировщик остановлен")
        except Exception as e:
            scheduler_logger.exception(f"Ошибка остановки планировщика: {e}")

    def get_next_runs(self) -> list[dict]:
        """Получить список планируемых запусков."""
        if not self.is_running:
            return []
        
        next_runs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                next_runs.append({
                    "job_id": job.id,
                    "next_run": next_run.isoformat(),
                })
        
        return next_runs


# Глобальный экземпляр планировщика
scheduler_instance: ReportScheduler | None = None


def get_scheduler() -> ReportScheduler:
    """Get или создать глобальный экземпляр планировщика."""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = ReportScheduler()
    return scheduler_instance
