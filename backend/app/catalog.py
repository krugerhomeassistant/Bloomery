"""Loggable tag catalog: single source of truth for backend + frontend (served at /api/catalog)."""

CATALOG: list[dict] = [
    {"id": "symptoms", "title": "Symptoms", "color": "#FF6F91", "items": [
        ("fine", "Everything is fine", "👍"), ("cramps", "Cramps", "🌀"), ("tender_breasts", "Tender breasts", "🍈"),
        ("headache", "Headache", "🤕"), ("acne", "Acne", "🔴"), ("backache", "Backache", "🦴"),
        ("fatigue", "Fatigue", "🥱"), ("cravings", "Cravings", "🍫"), ("insomnia", "Insomnia", "🌙"),
        ("abdominal_pain", "Abdominal pain", "😣"), ("vaginal_itching", "Vaginal itching", "🌵"),
        ("vaginal_dryness", "Vaginal dryness", "🏜️"), ("dizziness", "Dizziness", "💫"), ("hot_flashes", "Hot flashes", "🔥"),
        ("night_sweats", "Night sweats", "💦"), ("brain_fog", "Brain fog", "🌫️"), ("joint_pain", "Joint pain", "🦵"),
        ("palpitations", "Palpitations", "💓"),
    ]},
    {"id": "mood", "title": "Mood", "color": "#FFA940", "items": [
        ("calm", "Calm", "😌"), ("happy", "Happy", "😊"), ("energetic", "Energetic", "⚡"), ("frisky", "Frisky", "😏"),
        ("mood_swings", "Mood swings", "🎢"), ("irritated", "Irritated", "😤"), ("sad", "Sad", "😢"),
        ("anxious", "Anxious", "😰"), ("depressed", "Depressed", "😞"), ("guilty", "Feeling guilty", "😔"),
        ("obsessive", "Obsessive thoughts", "🔁"), ("low_energy", "Low energy", "🪫"), ("apathetic", "Apathetic", "😐"),
        ("confused", "Confused", "😵‍💫"), ("self_critical", "Very self-critical", "🪞"),
    ]},
    {"id": "sex", "title": "Sex and sex drive", "color": "#E84393", "items": [
        ("none", "Didn't have sex", "🚫"), ("protected", "Protected sex", "🛡️"), ("unprotected", "Unprotected sex", "💞"),
        ("oral", "Oral sex", "👄"), ("anal", "Anal sex", "🍑"), ("masturbation", "Masturbation", "✋"),
        ("sensual_touch", "Sensual touch", "🤲"), ("toys", "Sex toys", "🎀"), ("orgasm", "Orgasm", "🎆"),
        ("high_drive", "High sex drive", "📈"), ("neutral_drive", "Neutral sex drive", "➖"), ("low_drive", "Low sex drive", "📉"),
    ]},
    {"id": "discharge", "title": "Vaginal discharge", "color": "#9B7BF7", "items": [
        ("none", "No discharge", "⚪"), ("creamy", "Creamy", "🥛"), ("watery", "Watery", "💧"), ("sticky", "Sticky", "🍯"),
        ("egg_white", "Egg white", "🥚"), ("spotting", "Spotting", "🩸"), ("unusual", "Unusual", "⚠️"),
        ("clumpy", "Clumpy white", "☁️"), ("gray", "Gray", "🩶"),
    ]},
    {"id": "digestion", "title": "Digestion and stool", "color": "#20C997", "items": [
        ("nausea", "Nausea", "🤢"), ("bloating", "Bloating", "🎈"), ("constipation", "Constipation", "🧱"),
        ("diarrhea", "Diarrhea", "🌊"),
    ]},
    {"id": "activity", "title": "Physical activity", "color": "#3BA7F5", "items": [
        ("none", "Didn't exercise", "🛋️"), ("yoga", "Yoga", "🧘"), ("gym", "Gym", "🏋️"), ("aerobics", "Aerobics & dancing", "💃"),
        ("running", "Running", "🏃"), ("cycling", "Cycling", "🚴"), ("swimming", "Swimming", "🏊"),
        ("team_sports", "Team sports", "⚽"), ("walking", "Walking", "🚶"),
    ]},
    {"id": "pill", "title": "Oral contraceptives", "color": "#6C8EF5", "items": [
        ("taken", "Taken on time", "💊"), ("missed", "Missed pill", "⏰"), ("double", "Double dose", "✌️"),
    ]},
    {"id": "other", "title": "Other", "color": "#8E9AAF", "items": [
        ("travel", "Travel", "✈️"), ("stress", "Stress", "🌪️"), ("meditation", "Meditation", "🕯️"),
        ("journaling", "Journaling", "📓"), ("kegels", "Kegel exercises", "💪"), ("breathing", "Breathing exercises", "🌬️"),
        ("illness", "Disease or injury", "🤒"), ("alcohol", "Alcohol", "🍷"),
    ]},
    {"id": "ovulation_test", "title": "Ovulation test", "color": "#14B8A6", "items": [
        ("negative", "Test: negative", "➖"), ("positive", "Test: positive", "➕"), ("none", "Didn't take tests", "🚫"),
    ]},
    {"id": "pregnancy_test", "title": "Pregnancy test", "color": "#F472B6", "items": [
        ("negative", "Test: negative", "➖"), ("faint", "Faint line", "〰️"), ("positive", "Test: positive", "➕"),
        ("none", "Didn't take tests", "🚫"),
    ]},
]

FLOW = [("spotting", "Spotting", "🩸"), ("light", "Light", "💧"), ("medium", "Medium", "💧💧"), ("heavy", "Heavy", "💧💧💧")]


def catalog_json() -> dict:
    return {
        "flow": [{"id": i, "label": l, "emoji": e} for i, l, e in FLOW],
        "categories": [
            {**{k: v for k, v in c.items() if k != "items"},
             "items": [{"id": i, "label": l, "emoji": e} for i, l, e in c["items"]]}
            for c in CATALOG
        ],
    }


LABELS: dict[str, str] = {f"{c['id']}:{i}": l for c in CATALOG for i, l, _ in c["items"]}
VALID: dict[str, set[str]] = {c["id"]: {i for i, _, _ in c["items"]} for c in CATALOG}
