"""Urunden embedding metni kurma.

Neden ayri dosya: sira ve temizlik kategorizasyon kalitesini dogrudan belirliyor,
tek yerde ve test edilebilir olmali.

Olculen problem: metin `title + product_type + tags` seklinde kurulunca uzun
basliklar product_type'i hem gurultuye bogdu hem de max_seq_length sinirinda
sondan kirpti. Ayni product_type'a ('Saltele si Accesorii Infasat') sahip
urunler Food & Beverage, Lab & Measurement ve Water Sports'a dagildi.

Cozum: saticinin kendi siniflandirmasi (product_type) basa gelir - en guclu
sinyal odur; baslik olcu/model gurultusunden temizlenip arkaya eklenir.
"""
from __future__ import annotations

import re

# 70x50 cm, 6 luni+, 22 kg, 42 mm, 250ml gibi olcu ifadeleri.
_MEASURE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:x\s*\d+(?:[.,]\d+)?\s*)*"
    r"(?:cm|mm|m|kg|gr?|ml|l|lb|oz|inch|in|\"|''|luni|ani|years?|months?)\b",
    re.I,
)
# MTP-E510D-7AVDF, R8853100014, MK5735 gibi model/SKU kodlari.
_MODEL_CODE = re.compile(r"\b(?=[A-Z0-9-]*\d)[A-Z0-9][A-Z0-9-]{4,}\b")
# Ardisik bosluk/noktalama.
_PUNCT = re.compile(r"[\s,;|/·•\-–—]{2,}")


def clean_title(title: str) -> str:
    """Olcu ve model kodu gurultusunu atar, anlamli kelimeleri birakir."""
    t = _MEASURE.sub(" ", title or "")
    t = _MODEL_CODE.sub(" ", t)
    t = _PUNCT.sub(" ", t)
    return t.strip(" ,;-").strip()


def build_text(
    title: str,
    product_type: str | None,
    tags: list[str] | None,
    vendor: str | None = None,
) -> str:
    """Embedding'e verilecek metin. Sira: product_type -> baslik -> ek etiketler."""
    parts: list[str] = []
    seen: set[str] = set()

    def push(value: str | None, limit: int = 120) -> None:
        if not value:
            return
        v = value.strip()[:limit]
        key = v.casefold()
        if v and key not in seen:
            seen.add(key)
            parts.append(v)

    # 1) Saticinin kendi kategorisi - en guclu ve en kisa sinyal.
    push(product_type)

    # 2) Temizlenmis baslik.
    cleaned = clean_title(title)
    push(cleaned or (title or "").strip(), 160)

    # 3) Marka adi ve product_type'i tekrarlayan etiketler bilgi tasimaz; ele.
    vendor_key = (vendor or "").strip().casefold()
    extra = 0
    for tag in tags or []:
        if extra >= 6:
            break
        tag = str(tag).strip()
        key = tag.casefold()
        if not tag or key == vendor_key or key in seen:
            continue
        seen.add(key)
        parts.append(tag)
        extra += 1

    return ". ".join(parts)[:400]
