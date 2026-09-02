"""CT loglarindan gelen ham domain isimlerini eleyen saf fonksiyonlar.

Ayri dosyada, cunku hem certstream listener hem de manuel seeding ayni
kurallari kullaniyor ve bu kurallar test edilebilir olmali.
"""
from __future__ import annotations

# Sertifika yayinlayan ama magaza olmayan altyapi saglayicilari.
# Bunlarin altinda binlerce subdomain uretilir, kuyrugu doldurur.
INFRA_SUFFIXES: frozenset[str] = frozenset(
    {
        "amazonaws.com",
        "azurewebsites.net",
        "cloudapp.azure.com",
        "cloudflare.com",
        "cloudflaressl.com",
        "cloudfront.net",
        "digitaloceanspaces.com",
        "elasticbeanstalk.com",
        "fastly.net",
        "firebaseapp.com",
        "githubusercontent.com",
        "github.io",
        "gitlab.io",
        "googleapis.com",
        "googleusercontent.com",
        "herokuapp.com",
        "herokudns.com",
        "netlify.app",
        "netlify.com",
        "ngrok.io",
        "onmicrosoft.com",
        "pages.dev",
        "railway.app",
        "render.com",
        "repl.co",
        "sendgrid.net",
        "shopifycdn.com",
        "shopifypreview.com",
        "sslip.io",
        "storage.googleapis.com",
        "trafficmanager.net",
        "vercel.app",
        "web.app",
        "workers.dev",
        "wpengine.com",
        "zendesk.com",
    }
)

# Magaza olamayacak TLD'ler.
BLOCKED_TLDS: frozenset[str] = frozenset(
    {"gov", "edu", "mil", "int", "arpa", "gov.uk", "ac.uk", "edu.au", "gov.au"}
)

# example.co.uk gibi iki parcali son ekler: bunlarda 3 etiket = apex demektir.
MULTI_PART_SUFFIXES: frozenset[str] = frozenset(
    {
        "co.uk", "org.uk", "me.uk", "ltd.uk", "plc.uk",
        "com.au", "net.au", "org.au",
        "co.nz", "net.nz", "org.nz",
        "com.br", "com.mx", "com.ar", "com.co", "com.pe",
        "co.za", "co.il", "co.in", "co.id", "co.kr", "co.jp", "co.th",
        "com.tr", "net.tr", "org.tr",
        "com.sg", "com.my", "com.ph", "com.vn", "com.hk", "com.tw",
        "com.pl", "com.ua", "com.es", "com.pt", "com.gr", "com.ro",
        "com.sa", "com.eg", "com.ng", "com.pk", "com.bd",
    }
)

# Magaza olma ihtimali sifir olan tipik subdomain etiketleri.
NOISE_LABELS: frozenset[str] = frozenset(
    {
        "mail", "smtp", "imap", "pop", "webmail", "mx", "autodiscover", "autoconfig",
        "ns1", "ns2", "dns", "vpn", "ftp", "sftp", "cpanel", "whm", "webdisk",
        "api", "cdn", "static", "assets", "img", "images", "media",
        "dev", "test", "staging", "stage", "preview", "beta", "demo", "sandbox",
        "admin", "portal", "intranet", "git", "jenkins", "grafana", "kibana",
        "monitoring", "status", "mailer", "track", "click", "link", "email",
    }
)


def _registrable_suffix(labels: list[str]) -> int:
    """Kayit edilebilir alan adinin kac etiketten olustugunu dondurur (2 veya 3)."""
    if len(labels) >= 3 and ".".join(labels[-2:]) in MULTI_PART_SUFFIXES:
        return 3
    return 2


def normalize(raw: str) -> str | None:
    """Ham CT girdisini normalize eder; kabul edilmiyorsa None."""
    if not raw:
        return None
    d = raw.strip().lower().rstrip(".")

    # Wildcard sertifikalar: '*.example.com' -> 'example.com'
    if d.startswith("*."):
        d = d[2:]

    if not d or "/" in d or " " in d or ".." in d:
        return None
    if d.startswith(".") or d.endswith("."):
        return None

    # IDN punycode - karisik, cogunlukla spam. Ele.
    if "xn--" in d:
        return None

    labels = d.split(".")
    if len(labels) < 2:
        return None
    if any(not lb or len(lb) > 63 for lb in labels):
        return None
    if not all(c.isalnum() or c == "-" for lb in labels for c in lb):
        return None

    tld = labels[-1]
    if tld.isdigit() or len(tld) < 2:
        return None
    if tld in BLOCKED_TLDS or ".".join(labels[-2:]) in BLOCKED_TLDS:
        return None

    if any(d == suf or d.endswith("." + suf) for suf in INFRA_SUFFIXES):
        return None

    # 'www.' apex sayilir, kirp.
    if labels[0] == "www":
        labels = labels[1:]
        d = ".".join(labels)
        if len(labels) < 2:
            return None

    apex_len = _registrable_suffix(labels)

    # 3+ seviyeli subdomain (apex uzerine 2+ etiket) ele.
    if len(labels) > apex_len + 1:
        return None

    # Tek seviyeli subdomain varsa gurultu etiketi olmamali.
    if len(labels) == apex_len + 1 and labels[0] in NOISE_LABELS:
        return None

    return d


def extract(all_domains: list[str]) -> set[str]:
    """Bir sertifikadaki tum SAN girdilerinden kabul edilenleri dondurur."""
    out: set[str] = set()
    for raw in all_domains or []:
        norm = normalize(raw)
        if norm:
            out.add(norm)
    return out
