from __future__ import annotations

from typing import Literal


Locale = Literal["en", "ru"]
DEFAULT_LOCALE: Locale = "en"
SUPPORTED_LOCALES: tuple[Locale, ...] = ("en", "ru")
LOCALE_NAMES: dict[Locale, str] = {"en": "English", "ru": "Русский"}


TEXT: dict[Locale, dict[str, str]] = {
    "en": {
        "brand.by": "by PanCrucian",
        "link.label": "Video link",
        "link.placeholder": "Paste a YouTube link",
        "link.paste": "Paste",
        "link.error.not_youtube": "This isn’t a YouTube link. Copy the link from youtube.com or youtu.be.",
        "link.error.empty_clipboard": "The clipboard is empty. Copy the video’s link first.",
        "link.error.empty": "Paste a YouTube link first.",
        "range.start": "Start",
        "range.end": "End",
        "range.start.placeholder": "0:00",
        "range.end.placeholder": "to the end",
        "range.hint": "Seconds, M:SS or H:MM:SS",
        "range.full": "Whole video",
        "range.until": "Clip to {end}",
        "range.from": "Clip from {start}",
        "range.between": "Clip {start}–{end}",
        "folder.label": "Save to",
        "folder.change": "Change…",
        "folder.dialog": "Choose a folder for downloads",
        "exact.label": "Exact cut",
        "exact.hint": "Cuts on the exact frame, takes longer",
        "action.download_video": "Download video",
        "action.download_clip": "Download clip",
        "action.cancel": "Cancel",
        "action.show_file": "Show in folder",
        "action.retry": "Try again",
        "action.sign_in": "Sign in",
        "action.remove": "Remove",
        "action.dismiss": "Dismiss",
        "list.title": "Downloads",
        "list.clear": "Clear finished",
        "list.empty.title": "No downloads yet",
        "list.empty.body": "Paste a link above and press Download video. Leave Start and End empty to get the whole video.",
        "job.queued": "Waiting",
        "job.saved": "Saved",
        "job.cancelled": "Cancelled",
        "job.signed_in_retry": "Signed in. Try the download again.",
        "status.preparing": "Starting…",
        "status.working": "Working…",
        "status.checking_tools": "Checking components…",
        "status.fetching_info": "Reading video details…",
        "status.reading_cookie_file": "Using your YouTube session…",
        "status.starting_download": "Downloading…",
        "status.processing_file": "Processing the file…",
        "status.merging_video_audio": "Joining video and sound…",
        "status.merging_tracks": "Joining tracks…",
        "progress.size": "{downloaded} of {total}",
        "progress.eta": "{time} left",
        "session.signed_out": "YouTube: not signed in",
        "session.signed_in": "YouTube: signed in",
        "session.waiting": "YouTube: waiting for sign-in…",
        "session.sign_in": "Sign in",
        "session.sign_in_again": "Sign in again",
        "session.cancel": "Cancel",
        "notice.auth_started": "Sign in to Google in the browser window that just opened. Clipify keeps only the YouTube session, in a file next to the app. Your password stays with Google.",
        "notice.auth_success": "Signed in with {browser}. Downloads now use this YouTube session.",
        "unit.b": "B",
        "unit.kb": "KB",
        "unit.mb": "MB",
        "unit.gb": "GB",
        "unit.per_second": "{size}/s",
        "unit.seconds": "{s} s",
        "unit.minutes": "{m} min {s} s",
        "unit.minutes_only": "{m} min",
        "unit.hours": "{h} h {m} min",
        "error.time_format": "Use seconds, M:SS or H:MM:SS.",
        "error.time_numbers": "Use digits and colons only, like 1:05.",
        "error.time_negative": "Time can’t be negative.",
        "error.seconds_range": "Seconds must be 0–59.",
        "error.minutes_range": "Minutes must be 0–59.",
        "error.range_order": "End must be after start.",
        "error.youtube_auth_required": "YouTube asks you to sign in before downloading this video.",
        "error.youtube_session_expired": "Your YouTube session has expired. Sign in again.",
        "error.video_private": "This video is private. If the owner shared it with you, sign in to YouTube and try again.",
        "error.video_private_no_access": "This video is private, and your YouTube account has no access to it.",
        "error.video_members_only": "This video is only for channel members or Premium subscribers.",
        "error.video_not_started": "This stream hasn’t started yet. Try again once it’s live.",
        "error.video_unavailable": "This video is unavailable. It may have been removed or blocked in your region.",
        "error.link_broken": "This link doesn’t open a video. Copy the link from the video’s page.",
        "error.rate_limited": "YouTube is limiting requests right now. Wait a few minutes, then try again.",
        "error.network": "Can’t reach YouTube. Check your internet connection and try again.",
        "error.disk_full": "The disk is full. Free up space or choose another folder.",
        "error.folder_denied": "Clipify can’t save to this folder. Choose another one.",
        "error.output_path_too_long": "This folder’s path is too long for Windows. Choose a folder closer to the drive root, like C:\\Videos.",
        "error.ffmpeg_missing": "This copy of Clipify is missing its video processor. Download Clipify again from GitHub.",
        "error.download": "Couldn’t download this video. Check the link and your internet connection, then try again.",
        "error.download_exit": "The download stopped unexpectedly. Try again.",
        "error.unexpected_worker": "The download failed unexpectedly. Try again; details are in clipify.log.",
        "error.worker_read": "Clipify lost track of the download. Try again.",
        "error.start_download": "Couldn’t start the download. Try again; details are in clipify.log.",
        "error.auth_browser_missing": "Signing in needs Chrome, Edge or Brave. Install one of them and try again.",
        "error.auth_browser_start": "Couldn’t open the sign-in window. Try again; details are in clipify.log.",
        "error.auth_browser_closed": "The sign-in window closed before you finished. Sign in again.",
        "error.auth_timeout": "Sign-in timed out after 10 minutes. Start again when you’re ready.",
        "error.auth_not_signed_in": "Clipify didn’t find a YouTube sign-in. Try again.",
        "error.auth_failed": "Couldn’t sign in. Try again; details are in clipify.log.",
        "error.choose_folder": "Couldn’t open the folder picker. Details are in clipify.log.",
        "error.open_folder": "Couldn’t open the folder. It may have been moved or deleted.",
        "error.open_author": "Couldn’t open the link. Go to t.me/PanCrucian in your browser.",
        "error.system": "Unexpected error. Details are in {log}.",
        "error.missing_component": "Couldn’t load {component}. Clipify still works; details are in {log}.",
        "component.windows_icon": "the taskbar icon",
    },
    "ru": {
        "brand.by": "by PanCrucian",
        "link.label": "Ссылка на видео",
        "link.placeholder": "Вставьте ссылку на YouTube",
        "link.paste": "Вставить",
        "link.error.not_youtube": "Это не ссылка на YouTube. Скопируйте ссылку с youtube.com или youtu.be.",
        "link.error.empty_clipboard": "Буфер обмена пуст. Сначала скопируйте ссылку на видео.",
        "link.error.empty": "Сначала вставьте ссылку на YouTube.",
        "range.start": "Начало",
        "range.end": "Конец",
        "range.start.placeholder": "0:00",
        "range.end.placeholder": "до конца",
        "range.hint": "Секунды, М:СС или Ч:ММ:СС",
        "range.full": "Видео целиком",
        "range.until": "Фрагмент до {end}",
        "range.from": "Фрагмент с {start}",
        "range.between": "Фрагмент {start}–{end}",
        "folder.label": "Сохранить в",
        "folder.change": "Изменить…",
        "folder.dialog": "Выберите папку для загрузок",
        "exact.label": "Точная обрезка",
        "exact.hint": "Режет точно по кадру, но дольше",
        "action.download_video": "Скачать видео",
        "action.download_clip": "Скачать фрагмент",
        "action.cancel": "Отменить",
        "action.show_file": "Показать в папке",
        "action.retry": "Повторить",
        "action.sign_in": "Войти",
        "action.remove": "Убрать",
        "action.dismiss": "Скрыть",
        "list.title": "Загрузки",
        "list.clear": "Очистить завершённые",
        "list.empty.title": "Загрузок пока нет",
        "list.empty.body": "Вставьте ссылку выше и нажмите «Скачать видео». Если не указать начало и конец, скачается всё видео.",
        "job.queued": "В очереди",
        "job.saved": "Сохранено",
        "job.cancelled": "Отменено",
        "job.signed_in_retry": "Вход выполнен. Повторите загрузку.",
        "status.preparing": "Запускаем…",
        "status.working": "Работаем…",
        "status.checking_tools": "Проверяем компоненты…",
        "status.fetching_info": "Читаем данные видео…",
        "status.reading_cookie_file": "Подключаем вашу сессию YouTube…",
        "status.starting_download": "Скачиваем…",
        "status.processing_file": "Обрабатываем файл…",
        "status.merging_video_audio": "Соединяем видео и звук…",
        "status.merging_tracks": "Соединяем дорожки…",
        "progress.size": "{downloaded} из {total}",
        "progress.eta": "осталось {time}",
        "session.signed_out": "YouTube: вход не выполнен",
        "session.signed_in": "YouTube: вход выполнен",
        "session.waiting": "YouTube: ждём вход…",
        "session.sign_in": "Войти",
        "session.sign_in_again": "Войти заново",
        "session.cancel": "Отмена",
        "notice.auth_started": "Войдите в Google в открывшемся окне браузера. Clipify сохранит только сессию YouTube — в файле рядом с программой. Пароль остаётся у Google.",
        "notice.auth_success": "Вход через {browser} выполнен. Загрузки теперь используют эту сессию YouTube.",
        "unit.b": "Б",
        "unit.kb": "КБ",
        "unit.mb": "МБ",
        "unit.gb": "ГБ",
        "unit.per_second": "{size}/с",
        "unit.seconds": "{s} с",
        "unit.minutes": "{m} мин {s} с",
        "unit.minutes_only": "{m} мин",
        "unit.hours": "{h} ч {m} мин",
        "error.time_format": "Введите секунды, М:СС или Ч:ММ:СС.",
        "error.time_numbers": "Только цифры и двоеточия, например 1:05.",
        "error.time_negative": "Время не может быть отрицательным.",
        "error.seconds_range": "Секунды — от 0 до 59.",
        "error.minutes_range": "Минуты — от 0 до 59.",
        "error.range_order": "Конец должен быть позже начала.",
        "error.youtube_auth_required": "YouTube просит войти, чтобы скачать это видео.",
        "error.youtube_session_expired": "Сессия YouTube истекла. Войдите заново.",
        "error.video_private": "Это приватное видео. Если владелец открыл вам доступ, войдите в YouTube и повторите.",
        "error.video_private_no_access": "Это приватное видео, и у вашего аккаунта YouTube нет к нему доступа.",
        "error.video_members_only": "Видео доступно только спонсорам канала или подписчикам Premium.",
        "error.video_not_started": "Трансляция ещё не началась. Повторите, когда она пойдёт.",
        "error.video_unavailable": "Видео недоступно: его удалили или ограничили в вашем регионе.",
        "error.link_broken": "По этой ссылке нет видео. Скопируйте ссылку со страницы ролика.",
        "error.rate_limited": "YouTube временно ограничил запросы. Подождите несколько минут и повторите.",
        "error.network": "Нет связи с YouTube. Проверьте интернет и повторите.",
        "error.disk_full": "На диске нет места. Освободите место или выберите другую папку.",
        "error.folder_denied": "Clipify не может сохранять в эту папку. Выберите другую.",
        "error.output_path_too_long": "Путь к папке слишком длинный для Windows. Выберите папку ближе к корню диска, например C:\\Видео.",
        "error.ffmpeg_missing": "В этой копии Clipify нет обработчика видео. Скачайте Clipify заново с GitHub.",
        "error.download": "Не удалось скачать видео. Проверьте ссылку и интернет, затем повторите.",
        "error.download_exit": "Загрузка неожиданно прервалась. Повторите попытку.",
        "error.unexpected_worker": "Загрузка неожиданно сорвалась. Повторите; подробности — в clipify.log.",
        "error.worker_read": "Clipify потерял связь с загрузкой. Повторите попытку.",
        "error.start_download": "Не удалось начать загрузку. Повторите; подробности — в clipify.log.",
        "error.auth_browser_missing": "Для входа нужен Chrome, Edge или Brave. Установите один из них и повторите.",
        "error.auth_browser_start": "Не удалось открыть окно входа. Повторите; подробности — в clipify.log.",
        "error.auth_browser_closed": "Окно входа закрылось раньше времени. Войдите ещё раз.",
        "error.auth_timeout": "Вход не завершён за 10 минут. Начните заново, когда будете готовы.",
        "error.auth_not_signed_in": "Clipify не нашёл вход в YouTube. Попробуйте ещё раз.",
        "error.auth_failed": "Не удалось войти. Повторите; подробности — в clipify.log.",
        "error.choose_folder": "Не удалось открыть выбор папки. Подробности — в clipify.log.",
        "error.open_folder": "Не удалось открыть папку. Возможно, её переместили или удалили.",
        "error.open_author": "Не удалось открыть ссылку. Откройте t.me/PanCrucian в браузере.",
        "error.system": "Непредвиденная ошибка. Подробности — в {log}.",
        "error.missing_component": "Не удалось загрузить {component}. Clipify работает, подробности — в {log}.",
        "component.windows_icon": "значок на панели задач",
    },
}


def _selected(locale: str) -> Locale:
    return locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE  # type: ignore[return-value]


def translate(locale: str, key: str, **values: object) -> str:
    selected = _selected(locale)
    template = TEXT[selected].get(key) or TEXT[DEFAULT_LOCALE].get(key) or key
    return template.format(**values)


def format_number(value: float, locale: str, decimals: int = 1) -> str:
    text = f"{value:.{decimals}f}"
    return text.replace(".", ",") if _selected(locale) == "ru" else text


def format_size(size: float | None, locale: str) -> str:
    """Format a byte count the way Windows and macOS users read it (1024-based)."""

    if size is None or size < 0:
        return ""
    value = float(size)
    for unit, decimals in (("unit.b", 0), ("unit.kb", 0), ("unit.mb", 1)):
        if value < 1024:
            return f"{format_number(value, locale, decimals)} {translate(locale, unit)}"
        value /= 1024
    return f"{format_number(value, locale, 2)} {translate(locale, 'unit.gb')}"


def format_speed(bytes_per_second: float | None, locale: str) -> str:
    if not bytes_per_second or bytes_per_second <= 0:
        return ""
    return translate(locale, "unit.per_second", size=format_size(bytes_per_second, locale))


def format_duration(seconds: float | None, locale: str) -> str:
    if seconds is None or seconds < 0:
        return ""
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return translate(locale, "unit.hours", h=hours, m=minutes)
    if minutes >= 10 or (minutes and not secs):
        return translate(locale, "unit.minutes_only", m=minutes)
    if minutes:
        return translate(locale, "unit.minutes", m=minutes, s=secs)
    return translate(locale, "unit.seconds", s=secs)
