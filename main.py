import matplotlib
matplotlib.use('Agg')
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import feedparser
from newsapi import NewsApiClient
from groq import Groq
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === AKSJEPRISER ===
selskaper = {
    "Mowi": "MOWI.OL",
    "SalMar": "SALM.OL",
    "Lerøy": "LSG.OL"
}

alle_priser = {}
for navn, ticker in selskaper.items():
    data = yf.download(ticker, period="1y", interval="1wk", progress=False)
    alle_priser[navn] = data["Close"].squeeze()
    print(f"{navn} hentet ✅")

df = pd.DataFrame(alle_priser)
df_norm = (df / df.iloc[0]) * 100

# === SSB LAKSEPRIS OG VOLUM ===
ssb_url = "https://data.ssb.no/api/v0/no/table/03024"
ssb_query = {
    "query": [
        {"code": "VareGrupper2", "selection": {"filter": "item", "values": ["01"]}},
        {"code": "Tid", "selection": {"filter": "top", "values": ["12"]}}
    ],
    "response": {"format": "json-stat2"}
}

try:
    ssb_response = requests.post(ssb_url, json=ssb_query, timeout=10)
    ssb_data = ssb_response.json()
    perioder = list(ssb_data["dimension"]["Tid"]["category"]["label"].values())
    innhold = list(ssb_data["dimension"]["ContentsCode"]["category"]["label"].values())
    verdier = ssb_data["value"]
    n_perioder = len(perioder)
    kilopris_idx = innhold.index("Kilopris (kr)") if "Kilopris (kr)" in innhold else 1
    vekt_idx = innhold.index("Vekt (tonn)") if "Vekt (tonn)" in innhold else 0
    kilopriser = verdier[kilopris_idx * n_perioder:(kilopris_idx + 1) * n_perioder]
    volum = verdier[vekt_idx * n_perioder:(vekt_idx + 1) * n_perioder]
    laks_df = pd.DataFrame({
        "Periode": perioder,
        "Kilopris (kr)": kilopriser,
        "Volum (tonn)": volum
    })
    siste_pris = kilopriser[-1]
    prisendring = kilopriser[-1] - kilopriser[-2]
    siste_volum = volum[-1]
    volum_endring = volum[-1] - volum[-2]
    print(f"SSB laksepris hentet ✅ – siste pris: {siste_pris} kr/kg | volum: {siste_volum} tonn")
    ssb_ok = True
except Exception as e:
    print(f"SSB feilet: {e}")
    ssb_ok = False
    siste_pris = None
    prisendring = None
    siste_volum = None
    volum_endring = None

# === NORSKE RSS-FEEDS ===
norske_feeds = {
    "iLaks": "https://ilaks.no/feed/",
    "Fiskeribladet": "https://fiskeribladet.no/feed/",
    "Intrafish NO": "https://www.intrafish.no/rss",
    "NRK": "https://www.nrk.no/nyheter/siste.rss",
    "VG": "https://www.vg.no/rss/feed/?limit=20",
    "TV2": "https://www.tv2.no/rss/",
    "DN": "https://www.dn.no/rss",
}

relevante_ord = [
    "laks", "oppdrett", "sjømat", "fisk", "havbruk",
    "salmon", "aquaculture", "mowi", "salmar", "lerøy",
    "seafood", "sjømatnæring", "eksport", "akvakultur",
    "ilaks", "intrafish", "fiskeribladet"
]

norske_nyheter = []
for kilde, url in norske_feeds.items():
    try:
        feed = feedparser.parse(url)
        relevante = []
        for entry in feed.entries[:30]:
            tittel = entry.title.lower()
            if any(ord in tittel for ord in relevante_ord):
                relevante.append(f"[{kilde}] {entry.title}")
        norske_nyheter.extend(relevante[:4])
        print(f"{kilde}: {len(relevante)} relevante nyheter ✅")
    except Exception as e:
        print(f"{kilde} feilet: {e}")

# === INTERNASJONALE NYHETER VIA NEWSAPI ===
newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
internasjonale_nyheter = []

søkeord = [
    "salmon Norway price",
    "salmon aquaculture trade",
    "Norwegian salmon export"
]

for søk in søkeord:
    try:
        artikler = newsapi.get_everything(
            q=søk,
            language="en",
            sort_by="publishedAt",
            page_size=3
        )
        for a in artikler["articles"]:
            internasjonale_nyheter.append(f"[{a['source']['name']}] {a['title']}")
        print(f"NewsAPI '{søk}': {len(artikler['articles'])} nyheter ✅")
    except Exception as e:
        print(f"NewsAPI '{søk}' feilet: {e}")

alle_nyheter = norske_nyheter + internasjonale_nyheter
nyheter_tekst = "\n".join(alle_nyheter) if alle_nyheter else "Ingen nyheter tilgjengelig"
print(f"\nTotalt {len(alle_nyheter)} nyheter ({len(norske_nyheter)} norske, {len(internasjonale_nyheter)} internasjonale)")

# === GRAFER ===
n_grafer = 3 if ssb_ok else 2
fig, axes = plt.subplots(n_grafer, 1, figsize=(14, 6 * n_grafer))

for navn in selskaper.keys():
    axes[0].plot(df.index, df[navn], linewidth=2, label=navn)
axes[0].set_title("Aksjepris siste 12 måneder (NOK)", fontsize=13, fontweight="bold")
axes[0].set_ylabel("Pris (NOK)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

for navn in selskaper.keys():
    axes[1].plot(df_norm.index, df_norm[navn], linewidth=2, label=navn)
axes[1].axhline(y=100, color="gray", linestyle="--", alpha=0.5)
axes[1].set_title("Relativ utvikling siste 12 måneder (startpunkt = 100)", fontsize=13, fontweight="bold")
axes[1].set_ylabel("Indeksert verdi")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

if ssb_ok:
    ax2 = axes[2]
    ax2b = ax2.twinx()
    ax2.plot(laks_df["Periode"], laks_df["Kilopris (kr)"], color="#e63946", linewidth=2, marker="o", label="Kilopris (kr)")
    ax2b.bar(laks_df["Periode"], laks_df["Volum (tonn)"], alpha=0.3, color="#2196F3", label="Volum (tonn)")
    ax2.set_title(f"Laksepris & eksportvolum | Pris: {siste_pris} kr/kg | Volum: {siste_volum} tonn", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Kr per kg", color="#e63946")
    ax2b.set_ylabel("Tonn", color="#2196F3")
    ax2.tick_params(axis="x", rotation=45)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left")
    ax2b.legend(loc="upper right")

plt.tight_layout()
plt.savefig("lakseindustri.png", dpi=150)
print("Graf lagret!")

# === AI-ANALYSE ===
siste_priser = df.tail(10).to_string()
siste_norm = df_norm.tail(10).to_string()
ssb_tekst = laks_df.tail(10).to_string(index=False) if ssb_ok else "Ikke tilgjengelig"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

markedsanalyse = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""Du er en senior markedsanalytiker i sjømatbransjen som hjelper en lakseinnkjøper.

Aksjepriser siste 10 uker:
{siste_priser}

Relativ utvikling:
{siste_norm}

Laksepris og eksportvolum (SSB):
{ssb_tekst}

Siste laksepris: {siste_pris} kr/kg
Prisendring fra forrige uke: {prisendring:.2f} kr/kg
Eksportvolum siste uke: {siste_volum} tonn
Volumendring fra forrige uke: {volum_endring:.0f} tonn

Ferske nyheter:
{nyheter_tekst}

Gi følgende:
1. MARKEDSSTATUS: Kort oppsummering av hvor markedet er nå
2. PRISANALYSE: Hva sier pris og volum om pristrenden? Opp eller ned neste uke?
3. SELSKAPSOVERSIKT: Hvem presterer best/dårligst og hva betyr det for innkjøper?
4. FORHANDLINGSSTRATEGI: Konkrete argumenter innkjøper kan bruke overfor leverandør
5. ANBEFALT INNKJØPSPRIS: Hva bør innkjøper sikte på å betale per kg denne uken og hvorfor?"""
        }
    ]
)

pestel = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""Du er en senior markedsanalytiker i sjømatbransjen.
Lag en konkret PESTEL-analyse basert på disse nyhetene for lakseinnkjøpere i Norge:

{nyheter_tekst}

Siste laksepris: {siste_pris} kr/kg
Prisendring: {prisendring:.2f} kr/kg
Eksportvolum: {siste_volum} tonn
Volumendring: {volum_endring:.0f} tonn

Format:
P – Politisk: (konkrete punkter med prisimplikasjon)
E – Økonomisk: (konkrete punkter med prisimplikasjon)
S – Sosialt: (konkrete punkter med prisimplikasjon)
T – Teknologisk: (konkrete punkter med prisimplikasjon)
E – Miljø: (konkrete punkter med prisimplikasjon)
L – Legalt: (konkrete punkter med prisimplikasjon)

UKENS SIGNAL: Ett konkret råd til innkjøper."""
        }
    ]
)

print("\n=== MARKEDSANALYSE & FORHANDLINGSSTRATEGI ===")
print(markedsanalyse.choices[0].message.content)
print("\n=== PESTEL-ANALYSE ===")
print(pestel.choices[0].message.content)

# === E-POST ===
def send_rapport(markedsanalyse_tekst, pestel_tekst, graf_fil):
    sender = os.getenv("EMAIL_SENDER")
    passord = os.getenv("EMAIL_PASSWORD")
    mottaker = os.getenv("EMAIL_RECEIVER")
    dato = datetime.now().strftime("%d.%m.%Y")

    msg = MIMEMultipart("related")
    msg["Subject"] = f"🐟 Laksemarked ukesrapport – {dato}"
    msg["From"] = sender
    msg["To"] = mottaker

    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: auto;">
    <h1 style="color: #e63946;">🐟 Laksemarked – {dato}</h1>
    <p><b>Siste laksepris:</b> {siste_pris} kr/kg &nbsp;|&nbsp;
       <b>Endring:</b> {prisendring:.2f} kr/kg &nbsp;|&nbsp;
       <b>Eksportvolum:</b> {siste_volum} tonn</p>
    <img src="cid:graf" style="width:100%; border-radius:8px; margin: 20px 0;">
    <h2 style="color: #333;">📊 Markedsanalyse & Forhandlingsstrategi</h2>
    <pre style="background:#f5f5f5; padding:15px; border-radius:8px; white-space:pre-wrap;">{markedsanalyse_tekst}</pre>
    <h2 style="color: #333;">🌍 PESTEL-analyse</h2>
    <pre style="background:#f5f5f5; padding:15px; border-radius:8px; white-space:pre-wrap;">{pestel_tekst}</pre>
    <p style="color:#999; font-size:12px;">Automatisk generert av Salmon Market Intelligence Tool</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    with open(graf_fil, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", "<graf>")
        msg.attach(img)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, passord)
            server.sendmail(sender, mottaker, msg.as_string())
        print("E-post sendt ✅")
    except Exception as e:
        print(f"E-post feilet: {e}")

send_rapport(
    markedsanalyse.choices[0].message.content,
    pestel.choices[0].message.content,
    "lakseindustri.png"
)