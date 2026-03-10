import time
import requests
import os
# Fallback DG local (dans kenbot-runner)
try:
    from dg_text import build_facebook_dg, build_marketplace_dg
except Exception:
    build_facebook_dg = None
    build_marketplace_dg = None
def _cleanup(txt: str) -> str:
    t = (txt or "").strip()
    return t.replace("[[DG_FOOTER]]", "").strip()
def _is_too_short(txt: str) -> bool:
    return len((txt or "").strip()) < 200
def _is_too_long_for_marketplace(txt: str) -> bool:
    return len(txt) > 800
def generate_facebook_text(base_url: str, slug: str, event: str, vehicle: dict) -> str:
    """
    Version intelligente 2026 – la référence FB/Marketplace
    - AI prioritaire pour accroche naturelle (si activé)
    - Fallback DG enrichi + templates par marque
    - Marketplace auto-cut à 800 chars
    - Jamais vide : validation stricte + minimal vendeur
    - Logs détaillés pour debug Render
    """
    base_url = (base_url or "").strip()
    v = vehicle or {}
    # 1. Détection type véhicule (kind) pour personnaliser AI et hashtags
    try:
        from classifier import classify
        kind = classify(v)
    except ImportError:
        kind = "default"
        print(f"[WARN] classifier.py absent → kind fallback 'default' pour slug={slug}")
    # 2. Essai text-engine principal (kenbot-text-engine)
    base_txt = ""
    if base_url:
        url = f"{base_url.rstrip('/')}/generate"
        payload = {"slug": slug, "event": event, "vehicle": v}
        last_err = None
        for attempt in range(1, 5):
            try:
                r = requests.post(url, json=payload, timeout=180)
                r.raise_for_status()
                j = r.json() if r.content else {}
                txt = _cleanup(j.get("facebook_text") or j.get("text") or "")
                if txt and not _is_too_short(txt):
                    base_txt = txt
                    print(f"[DEBUG] Texte engine OK (len={len(txt)}) pour slug={slug}")
                    break
                print(f"[DEBUG] Texte engine vide/court (attempt {attempt}) → retry")
                time.sleep(3 * attempt)
            except Exception as e:
                last_err = str(e)
                print(f"[WARN] Tentative {attempt}/4 échouée pour slug={slug}: {last_err}")
                time.sleep(3 * attempt)
        if not base_txt:
            print(f"[DEBUG] Text-engine a échoué après 4 tentatives → fallback complet DG")
    else:
        print("[DEBUG] Pas d'URL text-engine → fallback direct DG")
    # 3. Bloc AI intelligent (prioritaire si activé)
    USE_AI = os.getenv("USE_AI", "0") == "1"
    ai_intro = ""
    if USE_AI and os.getenv("OPENAI_API_KEY"):
        try:
            from llm import generate_ad_text
            ai_intro = generate_ad_text(v, kind=kind, max_chars=180) # Réduit à 180 chars pour punch
            if ai_intro and ai_intro.strip():
                print(f"[DEBUG] AI intro ajoutée (len={len(ai_intro)}) pour slug={slug}: {ai_intro[:100]}...")
            else:
                print(f"[DEBUG] AI a renvoyé vide pour slug={slug} → skip AI")
        except ImportError as ie:
            print(f"[WARN] Impossible d'importer llm pour AI: {ie}")
        except Exception as e:
            print(f"[ERROR] Échec génération AI pour slug={slug}: {e}")
    # 4. Construction finale intelligente
    final_txt = []
    # Intro AI (si présente)
    if ai_intro:
        final_txt.append(ai_intro.strip())
        final_txt.append("")
    # Base texte engine (si présent) ou fallback DG boosté
    if base_txt:
        final_txt.append(base_txt)
    else:
        # Fallback DG boosté avec détection marque pour personnalisation
        if build_facebook_dg:
            dg_txt = build_facebook_dg(v)
            final_txt.append(dg_txt)
            print(f"[DEBUG] Fallback DG utilisé (len={len(dg_txt)}) pour slug={slug}")
        else:
            # Minimal ultra-vendeur si même DG absent
            minimal = (
                f"🔥 {v.get('title','Véhicule')} 🔥\n\n"
                f"💥 {v.get('price','Prix sur demande')} 💥\n"
                f"📊 {v.get('mileage','Km à confirmer')} 📊\n"
                f"🧾 Stock : {v.get('stock','---')} 🧾\n\n"
                f"✅ Inspecté et prêt à rouler ! Parfait pour la Beauce.\n"
                f"🔗 {v.get('url','https://kennebecdodge.ca')}\n"
                f"📞 Daniel Giroux – 418-222-3939\n"
                f"Écris-moi en privé ! #Beauce #AutoUsagée"
            )
            final_txt.append(minimal)
            print(f"[DEBUG] Fallback minimal ultra-vendeur pour slug={slug}")
    # 5. Version Marketplace courte si trop long
    full_text = "\n".join(final_txt).strip()
    if _is_too_long_for_marketplace(full_text):
        mp_txt = build_marketplace_dg(v) if build_marketplace_dg else full_text[:800].rstrip() + "…"
        print(f"[DEBUG] Texte trop long ({len(full_text)} chars) → version Marketplace courte générée")
        return mp_txt
    # 6. Validation finale : jamais vide, toujours vendeur
    if _is_too_short(full_text):
        print(f"[ERROR] Texte final trop court ({len(full_text)} chars) pour slug={slug} → force minimal")
        full_text = (
            f"🔥 {v.get('title','Véhicule')} 🔥\n"
            f"💥 Prix à discuter 💥\n"
            f"📞 Contacte-moi vite : 418-222-3939\n"
            f"Prêt pour la Beauce ! #Beauce #AutoUsagée"
        )
    return full_text
