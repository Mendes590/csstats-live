from __future__ import annotations
from typing import Optional, Dict, Any
import re
import contextlib

from playwright.sync_api import sync_playwright

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
    scope = txt[start:start+1400]
    rating = _first_int(scope)
    return rating


def scrape_player(steam_id: str) -> Dict[str, Any]:
    url = CSSTATS_BASE.format(steamid=steam_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        context = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            viewport={"width": 1440, "height": 900},
            locale="en-US",
            timezone_id="America/Sao_Paulo",
        )
        page = context.new_page()
        page.set_default_timeout(25000)

        page.goto(url, wait_until="domcontentloaded")
        with contextlib.suppress(Exception):
            page.wait_for_timeout(800)
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(300)
            page.evaluate("() => window.scrollTo(0, 0)")

        inner_text = ""
        with contextlib.suppress(Exception):
            inner_text = page.evaluate("() => document.body.innerText || ''") or ""

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
        # Try K/D card neighborhood
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
            import re as _re
            m = _re.search(r"K\/D[\\s\\S]{0,160}?(\\d+\\.\\d+)", inner_text, _re.I)
            if not m:
                m = _re.search(r"HLTV\\s*RATING[\\s\\S]{0,160}?(\\d+\\.\\d+)", inner_text, _re.I)
            if m:
                kd_value = float(m.group(1))

        browser.close()

    return {
        "steam_id": steam_id,
        "kd": kd_value,
        "csficacao": premier,
        "faceit_level": faceit_level,
        "csstats_profile": url,
    }


def scrape_premier_only(steam_id: str):
    d = scrape_player(steam_id)
    return {"premier": {"season": "S3", "rating": d.get("csficacao")}, "csstats_profile": d.get("csstats_profile")}
