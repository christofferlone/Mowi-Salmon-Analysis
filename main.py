import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

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

# Hent laksepris fra SSB
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
    n_innhold = len(innhold)
    
    kilopris_idx = innhold.index("Kilopris (kr)") if "Kilopris (kr)" in innhold else 1
    kilopriser = verdier[kilopris_idx * n_perioder:(kilopris_idx + 1) * n_perioder]
    
    laks_df = pd.DataFrame({"Periode": perioder, "Kilopris (kr)": kilopriser})
    print("SSB laksepris hentet ✅")
    print(laks_df.tail(5))
    ssb_ok = True
except Exception as e:
    print(f"SSB feilet: {e}")
    ssb_ok = False

# Grafer
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
    axes[2].plot(laks_df["Periode"], laks_df["Kilopris (kr)"], color="#e63946", linewidth=2, marker="o")
    axes[2].set_title("Norsk laksepris per kg – siste uker (SSB)", fontsize=13, fontweight="bold")
    axes[2].set_ylabel("Kr per kg")
    axes[2].tick_params(axis="x", rotation=45)
    axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("lakseindustri.png", dpi=150)
plt.show()
print("Graf lagret!")

siste_priser = df.tail(10).to_string()
siste_norm = df_norm.tail(10).to_string()
ssb_tekst = laks_df.tail(10).to_string(index=False) if ssb_ok else "Ikke tilgjengelig"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""Du er en senior analytiker i sjømatbransjen.
Analyser følgende data og gi et konkret innsikt:

Aksjepriser siste 10 uker (Mowi, SalMar, Lerøy):
{siste_priser}

Relativ utvikling (indeksert):
{siste_norm}

Laksepris per kg siste uker (SSB):
{ssb_tekst}

Gi et konkret innsikt:
1. Hvilke trender ser du på tvers av aksjepriser og laksepris?
2. Hvilket selskap presterer best/dårligst relativt sett?
3. Hva bør investorer og aktører i næringen merke seg?"""
        }
    ]
)

print("\n=== ANALYSE: NORSK LAKSEINDUSTRI ===")
print(chat.choices[0].message.content)