# Norwegian Salmon Market Intelligence Tool

An automated market analysis tool that aggregates live data from multiple sources and uses AI to generate actionable insights for salmon buyers and industry stakeholders in Norway.

## What it does

Runs automatically and produces:
- **Market analysis** with price trends, company performance and trading recommendations
- **PESTEL analysis** based on real-time news, with specific price implications per kg
- **Negotiation strategy** – concrete arguments a buyer can use to negotiate better prices
- **Recommended purchase price** based on current market data

## Data sources

| Source | Data |
|---|---|
| Yahoo Finance | Live stock prices – Mowi, SalMar, Lerøy (weekly, 12 months) |
| SSB (Statistics Norway) | Salmon export price per kg + export volume (tonnes) |
| NewsAPI | International salmon trade news |

## Example output

![Salmon Market Analysis](lakseindustri.png)

Three charts:
1. Absolute stock prices (NOK) – Mowi, SalMar, Lerøy
2. Relative performance (indexed, base = 100)
3. Export price per kg + export volume (dual axis)

## Tech stack

- Python
- yfinance, pandas, matplotlib (data and visualization)
- Groq API + LLaMA 3.3 70B (AI-powered analysis and PESTEL)
- SSB API (official Norwegian statistics)
- NewsAPI (international news)

## Setup

1. Clone the repository
2. Install dependencies: `pip install yfinance pandas matplotlib groq python-dotenv newsapi-python feedparser requests`
3. Create `.env` file with your API keys: `GROQ_API_KEY=your_key` and `NEWS_API_KEY=your_key`
4. Run: `python3 main.py`

## Relevance to aquaculture data analysis

This project demonstrates:
- **Automated data pipeline** – multiple live data sources aggregated in one script
- **LLM integration** – structured prompts generating domain-specific insights
- **Industry knowledge** – built by someone with 7 years of hands-on experience in Norwegian salmon farming (Lerøy Seafood)
- **Actionable output** – not just data, but decisions: what price to pay, how to negotiate, what market signals to watch

Next steps: integrate biological farming data (biomass, feed factor, growth rate) to support operational decision-making at farm level.

## Background

Built to explore AI integration in the aquaculture industry. The architecture is designed to scale – additional data sources (biological KPIs, weather, sea temperature) can be added modularly.