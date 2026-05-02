import requests
import pandas as pd
import matplotlib.pyplot as plt
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Selskaper vi analyserer
selskaper = {
    "Mowi": "MOWI.OL",
    "SalMar": "SALM.OL",
    "Lerøy": "LSG.OL"
}

headers = {"User-Agent": "Mozilla/5.0"}
alle_priser = {}

for navn, ticker in selskaper.items():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1wk&range=1y"
    response = requests.get(url, headers=headers, timeout=10)
    data = response.json()
    timestamps = data["chart"]["result"][0]["timestamp"]
    prices = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    datoer = pd.to_datetime(timestamps, unit="s")
    alle_priser[navn] = pd.Series(prices, index=datoer)
    print(f"{navn} hentet ✅")

df = pd.DataFrame(alle_priser)
df_norm = (df / df.iloc[0]) * 100

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

for navn in selskaper.keys():
    ax1.plot(df.index, df[navn], linewidth=2, label=navn)
ax1.set_title("Aksjepris siste 12 måneder (NOK)", fontsize=13, fontweight="bold")
ax1.set_ylabel("Pris (NOK)")
ax1.legend()
ax1.grid(True, alpha=0.3)

for navn in selskaper.keys():
    ax2.plot(df_norm.index, df_norm[navn], linewidth=2, label=navn)
ax2.axhline(y=100, color="gray", linestyle="--", alpha=0.5)
ax2.set_title("Relativ utvikling siste 12 måneder (startpunkt = 100)", fontsize=13, fontweight="bold")
ax2.set_ylabel("Indeksert verdi")
ax2.set_xlabel("Dato")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("lakseindustri.png", dpi=150)
plt.show()
print("Graf lagret!")

siste_priser = df.tail(10).to_string()
siste_norm = df_norm.tail(10).to_string()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""Du er en senior analytiker i sjømatbransjen.
Analyser aksjeprisutviklingen til Mowi, SalMar og Lerøy de siste 10 ukene.

Faktiske priser:
{siste_priser}

Relativ utvikling (indeksert):
{siste_norm}

Gi et konkret innsikt:
1. Hvilke trender ser du?
2. Hvilket selskap presterer best/dårligst relativt sett?
3. Hva bør investorer og aktører i næringen merke seg?"""
        }
    ]
)

print("\n=== ANALYSE: NORSK LAKSEINDUSTRI ===")
print(chat.choices[0].message.content)