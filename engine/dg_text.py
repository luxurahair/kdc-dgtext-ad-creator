# text_engine_client.py
import json
import os
import time
from typing import Any, Dict, Optional

import requests

from dg_text import build_facebook_dg, build_marketplace_dg

DOWN_FLAG_PATH = "/tmp/kenbot_text_engine_down_until"


def _now() -> float:
    return time.time()


def _read_down_until() -> float:
    try:
        with open(DOWN_FLAG_PATH, "r", encoding="utf-8") as f:
            return float(f.read().strip() or "0")
    except Exception:
        return 0.0


def _mark_down(seconds: int) -> None:
    try:
        until = _now() + max(30, int(seconds))
        with open(DOWN_FLAG_PATH, "w", encoding="utf-8") as f:
            f.write(str(until))
    except Exception:
        pass


def _is_down() -> bool:
    return _read_down_until() > _now()


def _sanitize_text(txt: str) -> str:
    txt = (txt or "").replace("[[DG_FOOTER]]", "").strip()
    # Normalise fins de ligne
    txt = "\n".join(line.rstrip() for line in txt.splitlines()).strip()
    return txt


def generate_facebook_text(
    base_url: str,
    slug: str,
    event: str,
    vehicle: Dict[str, Any],
    *,
    mode: str = "facebook",  # "facebook" ou "marketplace"
) -> str:
    """
    - mode="facebook": renvoie le texte COMPLET (pas de coupe marketplace)
    - mode="marketplace": peut raccourcir si trop long
    """
    mode = (mode or "facebook").strip().lower()
    base_url = (base_url or "").strip().rstrip("/")

    # Config
    timeout = int(os.getenv("KENBOT_TEXT_ENGINE_TIMEOUT", "45"))
    down_sec = int(os.getenv("KENBOT_TEXT_ENGINE_DOWN_SEC", "900"))  # 15 min
    max_retries = int(os.getenv("KENBOT_TEXT_ENGINE_MAX_RETRIES", "1"))  # IMPORTANT: pas 4
    retry_sleep = float(os.getenv("KENBOT_TEXT_ENGINE_RETRY_SLEEP", "2.5"))

    payload = {
        "slug": slug,
        "event": event,
        "vehicle": vehicle,
    }

    # 1) Tente text-engine si dispo
    txt: Optional[str] = None
    if base_url and not _is_down():
        url = f"{base_url}/generate"
        last_err = None

        for attempt in range(1, max_retries + 1):
            try:
                r = requests.post(url, json=payload, timeout=timeout)

                # 429 = coupe-circuit direct
                if r.status_code == 429:
                    _mark_down(down_sec)
                    raise RuntimeError(f"429 from text-engine (rate-limited). Cooldown {down_sec}s")

                # Si pas JSON, on traite comme panne
                ct = (r.headers.get("content-type") or "").lower()
                if r.status_code != 200 or "json" not in ct:
                    raise RuntimeError(f"text-engine bad response: HTTP={r.status_code} CT={ct}")

                data = r.json()
                txt = (data.get("facebook_text") or "").strip()
                txt = _sanitize_text(txt)

                if txt:
                    break

                raise RuntimeError("text-engine returned empty facebook_text")

            except Exception as e:
                last_err = e
                # pas de spam: une petite pause si on retente
                if attempt < max_retries:
                    time.sleep(retry_sleep)

        if txt is None and last_err is not None:
            # marque down si c'est une vraie panne réseau
            _mark_down(down_sec)

    # 2) Fallback DG (local) si text-engine down/ratelimit
    if not txt:
        fb_txt = _sanitize_text(build_facebook_dg(vehicle))
        txt = fb_txt

        # Option: intro AI (si tu veux garder ça dans le runner)
        if os.getenv("USE_AI", "").strip() == "1" and os.getenv("OPENAI_API_KEY", "").strip():
            try:
                from llm import generate_ad_text  # local kenbot-runner/llm.py

                ai_intro = generate_ad_text(vehicle, max_chars=220)
                ai_intro = _sanitize_text(ai_intro)
                if ai_intro:
                    txt = (ai_intro + "\n\n" + txt).strip()
            except Exception:
                pass

    # 3) Seulement si mode marketplace → on raccourcit
    if mode == "marketplace":
        if len(txt) > 800:
            mp_txt = _sanitize_text(build_marketplace_dg(vehicle))
            if mp_txt:
                txt = mp_txt

    return txt or ""
