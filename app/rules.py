APP_TITLE_ZH = "呦呦成长积分系统"
APP_TITLE_EN = "Yoyo Growth Points System"
CHILD_NAME_ZH = "呦呦"
CHILD_NAME_EN = "Yoyo"

WEEKLY_START_POINTS = 2
MAX_DAILY_EARN = 3
MAX_DAILY_DEDUCT = 2

EARNING_TASKS = [
    {
        "id": "learning",
        "label_zh": "学习任务",
        "label_en": "Learning",
        "detail_zh": "数学 / 德语 / 写字练习",
        "detail_en": "Math / German / handwriting practice",
        "points": 1,
    },
    {
        "id": "self_management",
        "label_zh": "自我管理",
        "label_en": "Self-management",
        "detail_zh": "整理书包文具",
        "detail_en": "Organize school bag and stationery",
        "points": 1,
    },
    {
        "id": "daily_habit",
        "label_zh": "生活习惯",
        "label_en": "Daily habit",
        "detail_zh": "吃饭认真，不掉饭",
        "detail_en": "Eat carefully and do not drop food",
        "points": 1,
    },
]

DEDUCTION_TASKS = [
    {
        "id": "lost_stationery",
        "label_zh": "丢文具",
        "label_en": "Lost stationery",
        "points": -1,
    },
    {
        "id": "messy_eating",
        "label_zh": "吃饭很乱",
        "label_en": "Messy eating",
        "points": -1,
    },
    {
        "id": "bag_not_organized",
        "label_zh": "提醒多次不整理书包",
        "label_en": "Did not organize school bag after reminders",
        "points": -1,
    },
    {
        "id": "delaying_tasks",
        "label_zh": "故意拖延任务",
        "label_en": "Delaying tasks on purpose",
        "points": -1,
    },
]

REWARD_TIERS = [
    {
        "id": "small_reward",
        "points": 12,
        "name_zh": "小玩具",
        "name_en": "Small toy",
        "desc_zh": "约 3-10 欧元的小玩具。",
        "desc_en": "A small toy around 3-10 EUR.",
    },
    {
        "id": "medium_reward",
        "points": 30,
        "name_zh": "中玩具",
        "name_en": "Medium toy",
        "desc_zh": "约 10-20 欧元的玩具。",
        "desc_en": "A toy around 10-20 EUR.",
    },
    {
        "id": "big_reward",
        "points": 38,
        "name_zh": "大玩具",
        "name_en": "Big toy",
        "desc_zh": "约 20-30 欧元的玩具。",
        "desc_en": "A bigger toy around 20-30 EUR.",
    },
]


def bi(zh: str, en: str) -> str:
    return f"{zh} / {en}"
