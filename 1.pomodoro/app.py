# Pomodoro Timer App
import json
import os
from datetime import date, timedelta
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# ─────────────────────────────────────────────
# XP / レベル設定
# ─────────────────────────────────────────────
XP_PER_POMODORO = 50
BASE_XP = 100  # レベル 1→2 に必要な基礎 XP


def xp_for_next_level(level: int) -> int:
    """レベルアップに必要な累積 XP（指数増加）"""
    return int(BASE_XP * (1.5 ** (level - 1)))


def calc_level(total_xp: int):
    """合計 XP からレベルと次レベルまでの進捗を返す"""
    level = 1
    accumulated = 0
    while True:
        needed = xp_for_next_level(level)
        if accumulated + needed > total_xp:
            current_xp = total_xp - accumulated
            return level, current_xp, needed
        accumulated += needed
        level += 1


# ─────────────────────────────────────────────
# バッジ定義
# ─────────────────────────────────────────────
BADGE_DEFINITIONS = [
    {
        "id": "first_pomodoro",
        "name": "はじめの一歩",
        "description": "初めてのポモドーロを完了",
        "icon": "🍅",
    },
    {
        "id": "streak_3",
        "name": "3日連続",
        "description": "3日連続でポモドーロを完了",
        "icon": "🔥",
    },
    {
        "id": "streak_7",
        "name": "一週間の継続",
        "description": "7日連続でポモドーロを完了",
        "icon": "⚡",
    },
    {
        "id": "weekly_10",
        "name": "週10達成",
        "description": "今週10回のポモドーロを完了",
        "icon": "🏆",
    },
    {
        "id": "total_50",
        "name": "熟練者",
        "description": "累計50回のポモドーロを完了",
        "icon": "🌟",
    },
    {
        "id": "total_100",
        "name": "マスター",
        "description": "累計100回のポモドーロを完了",
        "icon": "👑",
    },
    {
        "id": "level_5",
        "name": "レベル5到達",
        "description": "レベル5に達した",
        "icon": "🚀",
    },
    {
        "id": "level_10",
        "name": "レベル10到達",
        "description": "レベル10に達した",
        "icon": "💎",
    },
]


# ─────────────────────────────────────────────
# データ永続化
# ─────────────────────────────────────────────
def _default_data() -> dict:
    return {
        "total_xp": 0,
        "total_pomodoros": 0,
        "daily_records": {},   # "YYYY-MM-DD": count
        "earned_badges": [],
    }


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 旧データとのマージ（フィールド不足を補完）
        defaults = _default_data()
        for k, v in defaults.items():
            data.setdefault(k, v)
        return data
    return _default_data()


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# ストリーク計算
# ─────────────────────────────────────────────
def calc_streak(daily_records: dict) -> int:
    today = date.today()
    streak = 0
    current = today
    while True:
        key = current.isoformat()
        if daily_records.get(key, 0) > 0:
            streak += 1
            current -= timedelta(days=1)
        else:
            break
    return streak


# ─────────────────────────────────────────────
# バッジ判定
# ─────────────────────────────────────────────
def check_badges(data: dict) -> list[str]:
    """新たに獲得したバッジ ID のリストを返す。
    引数 data の 'earned_badges' フィールドも更新する（副作用あり）。
    """
    earned = set(data["earned_badges"])
    new_badges: list[str] = []
    streak = calc_streak(data["daily_records"])
    level, _, _ = calc_level(data["total_xp"])
    today_key = date.today().isoformat()
    week_start = date.today() - timedelta(days=date.today().weekday())
    weekly_count = sum(
        v
        for k, v in data["daily_records"].items()
        if k >= week_start.isoformat()
    )

    conditions = {
        "first_pomodoro": data["total_pomodoros"] >= 1,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "weekly_10": weekly_count >= 10,
        "total_50": data["total_pomodoros"] >= 50,
        "total_100": data["total_pomodoros"] >= 100,
        "level_5": level >= 5,
        "level_10": level >= 10,
    }

    for badge_id, cond in conditions.items():
        if cond and badge_id not in earned:
            earned.add(badge_id)
            new_badges.append(badge_id)

    data["earned_badges"] = list(earned)
    return new_badges


# ─────────────────────────────────────────────
# 統計計算
# ─────────────────────────────────────────────
def _week_labels_and_counts(daily_records: dict, offset_weeks: int = 0):
    today = date.today()
    week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=offset_weeks)
    labels = []
    counts = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        labels.append(d.strftime("%m/%d"))
        counts.append(daily_records.get(d.isoformat(), 0))
    return labels, counts


def _month_labels_and_counts(daily_records: dict, offset_months: int = 0):
    today = date.today()
    year = today.year
    month = today.month - offset_months
    while month <= 0:
        month += 12
        year -= 1
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    labels = []
    counts = []
    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        labels.append(str(day))
        counts.append(daily_records.get(d.isoformat(), 0))
    return labels, counts


# ─────────────────────────────────────────────
# ルート
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    data = load_data()
    level, current_xp, xp_needed = calc_level(data["total_xp"])
    streak = calc_streak(data["daily_records"])
    badge_map = {b["id"]: b for b in BADGE_DEFINITIONS}
    badges = [
        {**badge_map[b_id], "earned": True}
        for b_id in data["earned_badges"]
        if b_id in badge_map
    ]
    all_badges = [
        {**b, "earned": b["id"] in data["earned_badges"]}
        for b in BADGE_DEFINITIONS
    ]

    week_labels, week_counts = _week_labels_and_counts(data["daily_records"])
    month_labels, month_counts = _month_labels_and_counts(data["daily_records"])

    today_key = date.today().isoformat()
    week_start = date.today() - timedelta(days=date.today().weekday())
    weekly_total = sum(
        v
        for k, v in data["daily_records"].items()
        if k >= week_start.isoformat()
    )

    return jsonify(
        {
            "total_xp": data["total_xp"],
            "total_pomodoros": data["total_pomodoros"],
            "level": level,
            "current_xp": current_xp,
            "xp_needed": xp_needed,
            "streak": streak,
            "today_count": data["daily_records"].get(today_key, 0),
            "weekly_total": weekly_total,
            "badges": all_badges,
            "weekly_chart": {"labels": week_labels, "counts": week_counts},
            "monthly_chart": {"labels": month_labels, "counts": month_counts},
        }
    )


@app.route("/api/complete", methods=["POST"])
def complete_pomodoro():
    data = load_data()
    today_key = date.today().isoformat()

    data["total_xp"] += XP_PER_POMODORO
    data["total_pomodoros"] += 1
    data["daily_records"][today_key] = data["daily_records"].get(today_key, 0) + 1

    new_badges = check_badges(data)
    save_data(data)

    level, current_xp, xp_needed = calc_level(data["total_xp"])
    streak = calc_streak(data["daily_records"])

    return jsonify(
        {
            "xp_gained": XP_PER_POMODORO,
            "total_xp": data["total_xp"],
            "level": level,
            "current_xp": current_xp,
            "xp_needed": xp_needed,
            "streak": streak,
            "new_badges": [
                next(
                    (b for b in BADGE_DEFINITIONS if b["id"] == bid),
                    None,
                )
                for bid in new_badges
                if any(b["id"] == bid for b in BADGE_DEFINITIONS)
            ],
        }
    )


@app.route("/api/reset", methods=["POST"])
def reset_data():
    save_data(_default_data())
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5000)
