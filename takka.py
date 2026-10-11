import requests
from datetime import datetime, timedelta

# ASETUKSET
NTFY_TOPIC = "takkavahti"  # VAIHDA TÄHÄN OMA KANAVASI NIMI!
SIIRTO_JA_VERO = 6.5                  # Sähkönsiirto + vero snt/kWh
PUULAMMON_HINTA = 11.25               # Tulikiven koivulämpö snt/kWh

LAT = 61.05
LON = 28.18

def get_tomorrow_temp():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=temperature_2m_mean&timezone=auto"
    res = requests.get(url, timeout=10).json()
    return res["daily"]["temperature_2m_mean"][1]

def estimate_cop(temp_c):
    if temp_c >= 5:
        return 4.0
    elif temp_c >= 0:
        return 3.2
    elif temp_c >= -7:
        return 2.8
    elif temp_c >= -15:
        return 2.2
    else:
        return 1.7

def get_tomorrow_prices():
    url = "https://api.porssisahko.net/v1/latest-prices.json"
    res = requests.get(url, timeout=10).json()
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    prices = []
    for entry in res.get("prices", []):
        entry_time = datetime.fromisoformat(entry["startDate"])
        if entry_time.date() == tomorrow:
            prices.append(entry["price"])
    return prices

def send_alert(message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": "Takkanälytys!".encode("utf-8"),
            "Priority": "high",
            "Tags": "fire,wood"
        },
        timeout=10
    )

def main():
    prices = get_tomorrow_prices()
    if not prices:
        return

    avg_spot = sum(prices) / len(prices)
    max_spot = max(prices)
    temp = get_tomorrow_temp()
    cop = estimate_cop(temp)

    spot_threshold = (PUULAMMON_HINTA * cop) - SIIRTO_JA_VERO
    expensive_hours = [p for p in prices if p > spot_threshold]

    if len(expensive_hours) >= 4 or avg_spot > spot_threshold:
        msg = (
            f"Huomenna kannattaa lämmittää Tulikivi!\n"
            f"• Ennustettu sää: {temp:.1f} °C (Pumpun COP ~{cop:.1f})\n"
            f"• Puu voittaa pumpun, kun spot > {spot_threshold:.1f} snt/kWh\n"
            f"• Kalliita tunteja huomenna: {len(expensive_hours)} kpl\n"
            f"• Huomisen huippuhinta: {max_spot:.1f} snt/kWh"
        )
        send_alert(msg)

if __name__ == "__main__":
    main()
