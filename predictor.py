import pandas as pd
from collections import Counter, defaultdict

class LotteryForecastEngine:
    def __init__(self, draws):
        self.draws = [str(x).zfill(3) for x in draws if str(x).isdigit()]

    def digit_frequency(self):
        counter = Counter()
        for draw in self.draws:
            counter.update(draw)
        return counter

    def number_frequency(self):
        return Counter(self.draws)

    def pair_frequency(self):
        pairs = Counter()
        for draw in self.draws:
            pairs[draw[:2]] += 1
            pairs[draw[1:]] += 1
        return pairs

    def mirror_number(self, number):
        mirror = {
            "0": "5", "1": "6", "2": "7", "3": "8", "4": "9",
            "5": "0", "6": "1", "7": "2", "8": "3", "9": "4"
        }
        return "".join(mirror[d] for d in number)

    def score_number(self, number):
        digit_freq = self.digit_frequency()
        number_freq = self.number_frequency()
        pair_freq = self.pair_frequency()

        score = 0

        score += number_freq[number] * 12
        score += digit_freq[number[0]] * 1.5
        score += digit_freq[number[1]] * 1.5
        score += digit_freq[number[2]] * 1.5
        score += pair_freq[number[:2]] * 3
        score += pair_freq[number[1:]] * 3

        mirror = self.mirror_number(number)
        score += number_freq[mirror] * 6

        if len(set(number)) == 1:
            score += 8
        elif len(set(number)) == 2:
            score += 5

        recent = self.draws[:20]
        if number in recent:
            score += 10

        return round(score, 2)

    def generate_predictions(self, limit=25):
        candidates = [str(i).zfill(3) for i in range(1000)]

        scored = []
        for num in candidates:
            scored.append({
                "number": num,
                "score": self.score_number(num)
            })

        scored = sorted(scored, key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def summary_tables(self):
        return {
            "hot_digits": self.digit_frequency().most_common(10),
            "hot_numbers": self.number_frequency().most_common(20),
            "hot_pairs": self.pair_frequency().most_common(20)
        }
