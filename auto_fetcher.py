import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

STATE_SLUGS = {
"AL":"alabama","AK":"alaska","AZ":"arizona","AR":"arkansas","CA":"california","CO":"colorado",
"CT":"connecticut","DE":"delaware","DC":"district-of-columbia","FL":"florida","GA":"georgia",
"ID":"idaho","IL":"illinois","IN":"indiana","IA":"iowa","KS":"kansas","KY":"kentucky",
"LA":"louisiana","ME":"maine","MD":"maryland","MA":"massachusetts","MI":"michigan",
"MN":"minnesota","MS":"mississippi","MO":"missouri","MT":"montana","NE":"nebraska",
"NH":"new-hampshire","NJ":"new-jersey","NM":"new-mexico","NY":"new-york","NC":"north-carolina",
"ND":"north-dakota","OH":"ohio","OK":"oklahoma","OR":"oregon","PA":"pennsylvania",
"RI":"rhode-island","SC":"south-carolina","SD":"south-dakota","TN":"tennessee","TX":"texas",
"VT":"vermont","VA":"virginia","WA":"washington","WV":"west-virginia","WI":"wisconsin","WY":"wyoming"
}

HEADERS = {"User-Agent": "Mozilla/5.0 LotteryForecastEngineUltra/1.0"}

def fetch_lotteryusa_results(state_code, game="pick3", draw="both", limit=150):
    state_code = state_code.upper()
    if state_code not in STATE_SLUGS:
        raise ValueError("Unsupported state code.")

    slug = STATE_SLUGS[state_code]
    game_slug = "pick-3" if game.lower() == "pick3" else "pick-4"
    length = 3 if game.lower() == "pick3" else 4

    urls = []
    if draw.lower() in ["midday", "both"]:
        urls.append((f"https://www.lotteryusa.com/{slug}/{game_slug}-midday/", "midday"))
    if draw.lower() in ["evening", "both"]:
        urls.append((f"https://www.lotteryusa.com/{slug}/{game_slug}/", "evening"))

    rows = []
    date_pattern = r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})"

    for url, draw_name in urls:
        html = requests.get(url, headers=HEADERS, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

        matches = list(re.finditer(date_pattern, text))
        for idx, match in enumerate(matches):
            date_text = match.group(2)
            block_start = match.end()
            block_end = matches[idx + 1].start() if idx + 1 < len(matches) else min(len(text), block_start + 700)
            block = text[block_start:block_end]

            digits = re.findall(r"(?<!\d)(\d)(?!\d)", block)
            if len(digits) >= length:
                num = "".join(digits[:length])
                try:
                    date = datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
                except Exception:
                    date = date_text
                rows.append({"date": date, "state": state_code, "game": game.lower(), "draw": draw_name, "number": num})

    df = pd.DataFrame(rows).drop_duplicates()
    if not df.empty:
        df = df.head(limit)
    return df