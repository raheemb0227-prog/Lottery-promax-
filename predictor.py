import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from itertools import product

class LotteryForecastEngine:
    def __init__(self, df, game="pick3", state=None, draw=None):
        self.df = df.copy()
        self.df["number"] = self.df["number"].astype(str)

        if game == "pick3":
            self.length = 3
            self.max_number = 1000
        elif game == "pick4":
            self.length = 4
            self.max_number = 10000
        else:
            raise ValueError("game must be pick3 or pick4")

        self.game = game.lower()
        self.df = self.df[self.df["game"].str.lower() == self.game]

        if state:
            self.df = self.df[self.df["state"].str.upper() == state.upper()]

        if draw and draw.lower() != "both":
            self.df = self.df[self.df["draw"].str.lower() == draw.lower()]

        self.df["number"] = self.df["number"].str.zfill(self.length)
        self.numbers = self.df["number"].tolist()

        if len(self.numbers) < 20:
            raise ValueError("Not enough results found. Need at least 20 previous draws for Ultra mode.")

        self.candidates = [str(i).zfill(self.length) for i in range(self.max_number)]

    def _safe_counter(self, items):
        return Counter(items)

    def feature_scores(self, number, history=None):
        nums = history if history is not None else self.numbers
        if not nums:
            return {}

        all_digits = Counter("".join(nums))
        recent_10 = Counter("".join(nums[-10:]))
        recent_30 = Counter("".join(nums[-30:]))
        recent_60 = Counter("".join(nums[-60:]))

        position_counts = [Counter() for _ in range(self.length)]
        for n in nums:
            for i, d in enumerate(n):
                position_counts[i][d] += 1

        pairs = Counter()
        for n in nums:
            for i in range(len(n) - 1):
                pairs[n[i:i+2]] += 1
            if len(n) >= 3:
                pairs[n[0] + n[-1]] += 1

        sums = Counter(sum(map(int, n)) for n in nums)

        def root(n):
            s = sum(map(int, n))
            while s > 9:
                s = sum(map(int, str(s)))
            return s

        roots = Counter(root(n) for n in nums)

        transitions = defaultdict(Counter)
        for i in range(len(nums) - 1):
            transitions[nums[i]][nums[i + 1]] += 1

        last_num = nums[-1]

        # digit family / box history
        box_counts = Counter("".join(sorted(n)) for n in nums)

        # overdue exact
        if number not in nums:
            gap = len(nums)
        else:
            last_seen = len(nums) - 1 - nums[::-1].index(number)
            gap = len(nums) - last_seen

        digits = list(map(int, number))
        straight_seq = all(digits[i] + 1 == digits[i+1] for i in range(len(digits)-1))
        reverse_seq = all(digits[i] - 1 == digits[i+1] for i in range(len(digits)-1))

        pattern = 0
        if len(set(number)) == 1:
            pattern += 14
        elif len(set(number)) < len(number):
            pattern += 8
        if number == number[::-1]:
            pattern += 6
        if straight_seq or reverse_seq:
            pattern += 10

        return {
            "all_digit": sum(all_digits[d] for d in number),
            "recent10": sum(recent_10[d] for d in number),
            "recent30": sum(recent_30[d] for d in number),
            "recent60": sum(recent_60[d] for d in number),
            "position": sum(position_counts[i][d] for i, d in enumerate(number)),
            "pairs": sum(pairs[number[i:i+2]] for i in range(len(number)-1)) + pairs[number[0] + number[-1]],
            "sum": sums[sum(map(int, number))],
            "root": roots[root(number)],
            "gap": min(gap, 100),
            "pattern": pattern,
            "markov": transitions[last_num][number],
            "box": box_counts["".join(sorted(number))]
        }

    def score_number(self, number, weights, history=None):
        feats = self.feature_scores(number, history=history)
        return sum(feats[k] * weights.get(k, 0) for k in feats)

    def default_weights(self):
        return {
            "all_digit": 1.0,
            "recent10": 3.0,
            "recent30": 2.0,
            "recent60": 1.25,
            "position": 3.0,
            "pairs": 3.5,
            "sum": 2.0,
            "root": 1.5,
            "gap": 0.35,
            "pattern": 2.0,
            "markov": 30.0,
            "box": 2.0
        }

    def aggressive_weights(self):
        return {
            "all_digit": 0.75,
            "recent10": 5.0,
            "recent30": 3.0,
            "recent60": 1.0,
            "position": 4.0,
            "pairs": 5.0,
            "sum": 2.5,
            "root": 2.0,
            "gap": 0.20,
            "pattern": 3.0,
            "markov": 50.0,
            "box": 3.0
        }

    def overdue_weights(self):
        return {
            "all_digit": 1.0,
            "recent10": 1.0,
            "recent30": 1.5,
            "recent60": 1.5,
            "position": 2.0,
            "pairs": 2.0,
            "sum": 2.0,
            "root": 2.0,
            "gap": 1.0,
            "pattern": 2.0,
            "markov": 15.0,
            "box": 1.0
        }

    def all_weight_sets(self):
        base = self.default_weights()
        return {
            "Balanced Ultra": base,
            "Aggressive Momentum": self.aggressive_weights(),
            "Overdue Cycle": self.overdue_weights(),
            "Pair Heavy": {**base, "pairs": 6.0, "position": 4.0, "recent10": 2.5},
            "Recent Heat": {**base, "recent10": 6.0, "recent30": 3.5, "all_digit": 0.5},
            "Transition Heavy": {**base, "markov": 75.0, "pairs": 4.0},
            "Box Pattern": {**base, "box": 6.0, "pattern": 4.0, "pairs": 4.5},
        }

    def rank(self, weights=None, history=None, top_n=25):
        weights = weights or self.default_weights()
        scored = [(num, self.score_number(num, weights, history=history)) for num in self.candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:top_n]
        raw_scores = [s for _, s in top]
        max_s = max(raw_scores) if raw_scores else 1
        min_s = min(raw_scores) if raw_scores else 0

        normalized = []
        for num, raw in top:
            norm = 100 if max_s == min_s else 50 + ((raw - min_s) / (max_s - min_s)) * 50
            normalized.append((num, round(raw, 2), round(norm, 2), self.confidence_tier(norm)))
        return normalized

    def confidence_tier(self, normalized_score):
        if normalized_score >= 95:
            return "Elite"
        if normalized_score >= 88:
            return "Very Strong"
        if normalized_score >= 78:
            return "Strong"
        if normalized_score >= 65:
            return "Medium"
        return "Low"

    def boxed_from_ranked(self, ranked, top_n=15):
        boxed = {}
        for num, raw, norm, tier in ranked:
            key = "".join(sorted(num))
            boxed[key] = boxed.get(key, 0) + raw
        results = sorted(boxed.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [(box, round(score, 2)) for box, score in results]

    def backtest_weight_set(self, weights, top_values=(10, 25, 50), max_tests=150):
        nums = self.numbers
        start = max(30, len(nums) - max_tests)
        results = {
            "tested_draws": 0,
            "top10_straight": 0,
            "top25_straight": 0,
            "top50_straight": 0,
            "top10_boxed": 0,
            "top25_boxed": 0,
            "top50_boxed": 0,
        }

        for i in range(start, len(nums)):
            history = nums[:i]
            actual = nums[i]
            if len(history) < 20:
                continue

            ranked = self.rank(weights=weights, history=history, top_n=max(top_values))
            picks = [x[0] for x in ranked]
            actual_box = "".join(sorted(actual))

            results["tested_draws"] += 1

            for tv in top_values:
                key_s = f"top{tv}_straight"
                key_b = f"top{tv}_boxed"
                top_picks = picks[:tv]
                top_boxes = {"".join(sorted(x)) for x in top_picks}

                if actual in top_picks:
                    results[key_s] += 1
                if actual_box in top_boxes:
                    results[key_b] += 1

        tested = results["tested_draws"]
        if tested == 0:
            return results

        for k in list(results.keys()):
            if k != "tested_draws":
                results[k] = round((results[k] / tested) * 100, 2)

        return results

    def tune_best_model(self):
        candidates = self.all_weight_sets()
        scored = []
        for name, weights in candidates.items():
            bt = self.backtest_weight_set(weights)
            # Prioritize boxed Top25 + straight Top25 + boxed Top10.
            objective = (bt.get("top25_boxed", 0) * 2.0) + bt.get("top25_straight", 0) + bt.get("top10_boxed", 0)
            scored.append((name, weights, bt, objective))
        scored.sort(key=lambda x: x[3], reverse=True)
        return scored

    def ensemble_predict(self, top_n=25):
        tuned = self.tune_best_model()
        combined = defaultdict(float)

        # combine top 3 performing models
        for rank_idx, (name, weights, bt, objective) in enumerate(tuned[:3]):
            model_weight = max(1, 3 - rank_idx)
            ranked = self.rank(weights=weights, top_n=150)
            for num, raw, norm, tier in ranked:
                combined[num] += norm * model_weight

        final = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_n]
        max_s = max([s for _, s in final]) if final else 1
        min_s = min([s for _, s in final]) if final else 0

        output = []
        for num, score in final:
            norm = 100 if max_s == min_s else 50 + ((score - min_s) / (max_s - min_s)) * 50
            output.append((num, round(score, 2), round(norm, 2), self.confidence_tier(norm)))
        return output, tuned