import asyncio
import re
from datetime import datetime, timedelta
from html import unescape
from typing import List
from urllib.parse import quote

import feedparser
from bs4 import BeautifulSoup

from config import settings
from database.models import RawNews
from utils.helpers import GeoError, get_geo_info, validate_geo
from utils.logger import news_logger

# Локальные RSS (без Google News — он собирается отдельно с правильным ceid/hl)
RSS_FEEDS: dict[str, list[str]] = {
    "BR": [
        "https://g1.globo.com/rss/g1/",
        "https://www.uol.com.br/rss/",
    ],
    "MX": [
        "https://www.eluniversal.com.mx/rss.xml",
    ],
}

# Поисковый запрос для Google News (не код страны — «BR» даёт тикер Broadridge)
GEO_NEWS_QUERIES: dict[str, str] = {
    "AR": "Argentina",
    "BO": "Bolivia",
    "BR": "Brasil",
    "CL": "Chile",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "DO": "República Dominicana",
    "EC": "Ecuador",
    "GT": "Guatemala",
    "HN": "Honduras",
    "MX": "México",
    "NI": "Nicaragua",
    "PA": "Panamá",
    "PE": "Perú",
    "PY": "Paraguay",
    "SV": "El Salvador",
    "UY": "Uruguay",
    "VE": "Venezuela",
    "IN": "India",
    "ID": "Indonesia",
    "PH": "Philippines",
    "TH": "Thailand",
    "VN": "Vietnam",
    "NG": "Nigeria",
    "ZA": "South Africa",
    "KE": "Kenya",
}

# ceid для Google News RSS (формат region:locale)
GEO_GOOGLE_CEID: dict[str, str] = {
    "BR": "BR:pt-419",
    "MX": "MX:es-419",
    "AR": "AR:es-419",
    "CO": "CO:es-419",
    "CL": "CL:es-419",
    "PE": "PE:es-419",
    "IN": "IN:en-IN",
    "ID": "ID:id",
    "PH": "PH:en-PH",
    "TH": "TH:th",
    "VN": "VN:vi",
    "NG": "NG:en-NG",
    "ZA": "ZA:en-ZA",
    "KE": "KE:en-KE",
}


def _google_ceid(geo: str, gl: str, hl: str) -> str:
    return GEO_GOOGLE_CEID.get(geo, f"{gl}:{hl}")


def _clean_text(html: str) -> str:
    """Убрать HTML из summary — AI получает чистый текст."""
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.lower().strip())


def _parse_entry_date(entry) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6])
    if getattr(entry, "updated_parsed", None):
        return datetime(*entry.updated_parsed[:6])
    return None


def _entry_to_raw_news(
    entry,
    *,
    source: str,
    source_type: str,
    cutoff_date: datetime,
) -> RawNews | None:
    title = (getattr(entry, "title", None) or "").strip()
    url = (getattr(entry, "link", None) or "").strip()
    if not title or not url:
        return None

    pub_date = _parse_entry_date(entry)
    if pub_date and pub_date < cutoff_date:
        return None

    snippet = _clean_text(entry.get("summary", entry.get("description", "")))

    return RawNews(
        title=title,
        url=url,
        date=(pub_date or datetime.now()).strftime("%Y-%m-%d"),
        snippet=snippet,
        source=source,
        source_type=source_type,
    )


async def _fetch_feed(url: str):
    """feedparser блокирующий — выносим в поток, чтобы не стопорить asyncio."""
    return await asyncio.to_thread(feedparser.parse, url)


async def parse_google_news(geo: str, days_back: int | None = None) -> List[RawNews]:
    """
    Парсинг Google News RSS для конкретного GEO.
    """
    geo = validate_geo(geo)
    if days_back is None:
        days_back = settings.NEWS_DAYS_BACK

    info = get_geo_info(geo)
    query = GEO_NEWS_QUERIES.get(geo, info["name"])
    hl = info["hl"]
    gl = info["gl"]
    ceid = _google_ceid(geo, gl, hl)

    news_logger.info(
        f"Google News: geo={geo}, query={query!r}, hl={hl}, gl={gl}, days={days_back}"
    )

    url = (
        f"https://news.google.com/rss/search?q={quote(query)}"
        f"&hl={hl}&gl={gl}&ceid={ceid}"
    )

    try:
        feed = await _fetch_feed(url)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        news_items: list[RawNews] = []

        for entry in feed.entries:
            item = _entry_to_raw_news(
                entry,
                source="Google News",
                source_type="google_news",
                cutoff_date=cutoff_date,
            )
            if item:
                news_items.append(item)

        news_logger.info(f"Google News: {len(news_items)} новостей")
        return news_items

    except Exception as e:
        news_logger.exception(f"Ошибка парсинга Google News для {geo}: {e}")
        return []


async def parse_rss_feeds(feed_urls: List[str], days_back: int | None = None) -> List[RawNews]:
    """Универсальный парсер RSS лент."""
    if days_back is None:
        days_back = settings.NEWS_DAYS_BACK

    news_logger.info(f"Парсинг {len(feed_urls)} RSS лент")
    all_news: list[RawNews] = []
    cutoff_date = datetime.now() - timedelta(days=days_back)

    for feed_url in feed_urls:
        try:
            news_logger.debug(f"RSS: {feed_url}")
            feed = await _fetch_feed(feed_url)
            source_name = feed.feed.get("title", feed_url)
            count_before = len(all_news)

            for entry in feed.entries:
                item = _entry_to_raw_news(
                    entry,
                    source=source_name,
                    source_type="rss",
                    cutoff_date=cutoff_date,
                )
                if item:
                    all_news.append(item)

            news_logger.debug(
                f"RSS {feed_url}: +{len(all_news) - count_before} новостей"
            )

        except Exception as e:
            news_logger.exception(f"Ошибка RSS {feed_url}: {e}")
            continue

    news_logger.info(f"RSS всего: {len(all_news)} новостей")
    return all_news


def deduplicate_news(news_items: List[RawNews]) -> List[RawNews]:
    """Дедупликация по URL и нормализованному заголовку."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique_news: list[RawNews] = []

    for news in news_items:
        norm_title = _normalize_title(news.title)
        if news.url in seen_urls or norm_title in seen_titles:
            continue
        seen_urls.add(news.url)
        seen_titles.add(norm_title)
        unique_news.append(news)

    news_logger.info(
        f"Дедупликация: {len(news_items)} → {len(unique_news)} новостей"
    )
    return unique_news


def filter_by_keywords(news_items: List[RawNews], keywords: List[str]) -> List[RawNews]:
    """Опциональная фильтрация — по умолчанию не используется в aggregate_news."""
    if not keywords:
        return news_items

    filtered = []
    for news in news_items:
        text = f"{news.title} {news.snippet}".lower()
        if any(keyword.lower() in text for keyword in keywords):
            filtered.append(news)

    news_logger.info(f"Фильтр по ключевым словам: {len(filtered)}/{len(news_items)}")
    return filtered


def _sort_by_date_desc(news_items: List[RawNews]) -> List[RawNews]:
    return sorted(news_items, key=lambda n: n.date, reverse=True)


async def aggregate_news(geo: str, days_back: int | None = None) -> List[RawNews]:
    """
    Агрегация новостей из всех источников для GEO.
    Возвращает список RawNews, готовый для передачи в AI.
    """
    try:
        geo = validate_geo(geo)
    except GeoError as e:
        news_logger.error(str(e))
        raise

    if days_back is None:
        days_back = settings.NEWS_DAYS_BACK

    news_logger.info(f"Агрегация новостей для {geo}, период {days_back} дн.")

    all_news: list[RawNews] = []

    all_news.extend(await parse_google_news(geo, days_back))

    if geo in RSS_FEEDS:
        all_news.extend(await parse_rss_feeds(RSS_FEEDS[geo], days_back))

    unique_news = deduplicate_news(all_news)
    unique_news = _sort_by_date_desc(unique_news)

    if settings.NEWS_MAX_ITEMS and len(unique_news) > settings.NEWS_MAX_ITEMS:
        news_logger.info(f"Ограничение до {settings.NEWS_MAX_ITEMS} (самые свежие)")
        unique_news = unique_news[: settings.NEWS_MAX_ITEMS]

    news_logger.info(f"Итого для {geo}: {len(unique_news)} новостей")
    return unique_news
