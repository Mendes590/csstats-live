# app/scrape.py
from __future__ import annotations
from typing import Optional, Dict, Any
import re
import contextlib
import time
import threading

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError, Error as PWError

CSSTATS_BASE = "https://csstats.gg/player/{steamid}"

NUM_GROUPED = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d{3,6})\b")
DECIMAL = re.compile(r"\b\d+\.\d+\b")
FACEIT_LEVEL = re.compile(r"faceit/level(\d+)\.png", re.I)

def _to_int(s: str) -> Optional[int]:
    try:
        return int(s.replace(",", ""))
    except Exception:
        return None

def _first_int(text: str) -> Optional[int]:
    m = NUM_GROUPED.search(text or "")
    return _to_int(m.group(1)) if m else None

def _first_decimal(text: str) -> Optional[float]:
    m = DECIMAL.search(text or "")
    return float(m.group(0)) if m else None

def _extract_premier(inner_text: str) -> Optional[int]:
    txt = inner_text or ""
    hit = re.search(r"Premier\s*-\s*Season\s*3|Premier[\s\S]{0,200}\bS3\b", txt, re.I)
    if not hit:
        return _first_int(txt)
    start = hit.start()
    scope = txt[start:start + 1400]
    rating = _first_int(scope)
    return rating

LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    # IMPORTANTE: em instâncias muito magras, o --single-process pode instabilizar.
    # Vamos REMOVER para ficar mais estável no Koyeb Free.
    # "--single-process",
    # "--no-zygote",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-default-apps",
    "--disable-features=Translate,AcceptCHFrame,MediaRouter",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-first-run",
    "--safebrowsing-disable-auto-update",
    "--js-flags=--max-old-space-size=128",
]

# ---------- Singleton Playwright Manager (browser global + fila) ----------

class _PWManager:
    _lock = threading.RLock()
    _inited = False
    _play = None
    _browser = None
    _context = None
    _semaphore = threading.Semaphore(1)  # 1 requisição por vez

    @classmethod
    def start(cls):
        with cls._lock:
            if cls._inited:
                return
            cls._play = sync_playwright().start()
            browser = cls._play.chromium.launch(headless=True, args=LAUNCH_ARGS)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="America/Sao_Paulo",
            )

            # Bloquear assets pesados
            def _router(route):
                rtype = route.request.resource_type
                if rtype in {"image", "media", "font"}:
                    return route.abort()
                return route.continue_()

            context.route("**/*", _router)

            cls._browser = browser
            cls._context = context
            cls._inited = True

    @classmethod
    def stop(cls):
        with cls._lock:
            if not cls._inited:
                return
            with contextlib.suppress(Exception):
                if cls._context:
                    cls._context.close()
            with contextlib.suppress(Exception):
                if cls._browser:
                    cls._browser.close()
            with contextlib.suppress(Exception):
                if cls._play:
                    cls._play.stop()
            cls._browser = None
            cls._context = None
            cls._play = None
            cls._inited = False

    @classmethod
    def with_page(cls):
        # garante inicializado
        if not cls._inited:
            cls.start()
        # 1 por vez no Free
        return cls._semaphore, cls._context.new_page()

# ---------- Scraping helpers ----------

def _goto_with_retries(page, url: str, tries: int = 2, wait_state: str = "domcontentloaded"):
    last = None
    for i in range(tries):
        try:
            page.set_default_timeout(45000)
            page.set_default_navigation_timeout(45000)
            page.goto(url, wait_until=wait_state)
            with contextlib.suppress(Exception):
                page.wait_for_timeout(500)
                page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(250)
                page.evaluate("() => window.scrollTo(0, 0)")
            return
        except (PWTimeoutError, PWError) as e:
            last = e
            page.wait_for_timeout(400)
            # Em caso de page crash, recria a page e tenta de novo:
            try:
                page = page.context.new_page()
            except Exception:
                pass
    if last:
        raise last

def _extract_values(page, inner_text: str) -> Dict[str, Any]:
    premier = _extract_premier(inner_text)

    faceit_level = None
    try:
        img = page.locator('img.rank[src*="faceit/level"]').first
        if img and img.count() > 0:
            src = img.get_attribute("src") or ""
            m = FACEIT_LEVEL.search(src)
            if m:
                faceit_level = int(m.group(1))
    except Exception:
        pass

    kd_value = None
    try:
        kd_block = page.locator('css=*, text=/^\\s*K\\/D\\s*$/i').first
        if kd_block and kd_block.count() > 0:
            kd_parent = kd_block.locator("xpath=..")
            for _ in range(4):
                txts = kd_parent.locator("xpath=.//span").all_inner_texts()
                nums = [t.strip() for t in txts if DECIMAL.search(t.strip())]
                if nums:
                    kd_value = float(DECIMAL.search(nums[0]).group(0))
                    break
                kd_parent = kd_parent.locator("xpath=..")
    except Exception:
        pass

    if kd_value is None:
        try:
            hltv_block = page.locator('css=*, text=/HLTV\\s*RATING/i').first
            if hltv_block and hltv_block.count() > 0:
                h_parent = hltv_block.locator("xpath=..")
                for _ in range(4):
                    txts = h_parent.locator("xpath=.//span").all_inner_texts()
                    nums = [t.strip() for t in txts if DECIMAL.search(t.strip())]
                    if nums:
                        kd_value = float(DECIMAL.search(nums[0]).group(0))
                        break
                    h_parent = h_parent.locator("xpath=..")
        except Exception:
            pass

    if kd_value is None:
        m = re.search(r"K\/D[\s\S]{0,160}?(\d+\.\d+)", inner_text, re.I) \
            or re.search(r"HLTV\s*RATING[\s\S]{0,160}?(\d+\.\d+)", inner_text, re.I)
        if m:
            kd_value = float(m.group(1))

    return {"kd": kd_value, "csficacao": premier, "faceit_level": faceit_level}

# ---------- API-level functions ----------

def scrape_player(steam_id: str) -> Dict[str, Any]:
    url = CSSTATS_BASE.format(steamid=steam_id)

    # 1 por vez no Free (evita matar o browser)
    sema, page = _PWManager.with_page()
    with sema:
        last_err = None
        try:
            _goto_with_retries(page, url, tries=2, wait_state="domcontentloaded")

            inner_text = ""
            with contextlib.suppress(Exception):
                inner_text = page.evaluate("() => document.body.innerText || ''") or ""

            data = _extract_values(page, inner_text)
            data.update({"steam_id": steam_id, "csstats_profile": url})
            return data
        except PWError as e:
            last_err = e
            # Se o alvo fechou, tenta uma única vez recriar tudo:
            _PWManager.stop()
            _PWManager.start()
            # Re-tenta uma vez:
            sema2, page2 = _PWManager.with_page()
            with sema2:
                _goto_with_retries(page2, url, tries=1, wait_state="domcontentloaded")
                inner_text = page2.evaluate("() => document.body.innerText || ''") or ""
                data = _extract_values(page2, inner_text)
                data.update({"steam_id": steam_id, "csstats_profile": url})
                return data
        finally:
            with contextlib.suppress(Exception):
                page.close()

def scrape_premier_only(steam_id: str):
    d = scrape_player(steam_id)
    return {"premier": {"season": "S3", "rating": d.get("csficacao")}, "csstats_profile": d.get("csstats_profile")}
