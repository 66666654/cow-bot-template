"""
随机事件调度器 v3
- 每天运行一次，随机抽取 3 个时间 + 3 个事件
- 30+ 个事件预设，覆盖 8 种场景类型
- 自动避开已使用的场景，保证多样性
- 时段智能匹配（深夜不推送白天事件，反之亦然）
"""
import json, random, os
from datetime import datetime
from croniter import croniter

TASKS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scheduler", "tasks.json")
RECEIVER = "对方微信ID"

# 每天 3 个随机时段
SLOT_COUNT = 3

# 候选时间池（24小时制）
CANDIDATE_TIMES = [
    "09:00", "09:30", "10:00", "10:30", "11:00",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
    "17:00", "17:30", "18:30", "19:00", "19:30", "20:00", "20:30",
    "21:00", "21:30", "22:30", "23:00",
]

# ============ 事件池（30+ 预设）============
EVENTS = {
    "闲聊分享": [
        "你刚在路上看到一只超可爱的猫/狗，忍不住想告诉对方。描述一下它长什么样、在干嘛，语气兴奋一点。以你的Bot身份，。",
        "你刷手机看到一条有趣的新闻/热搜，觉得对方也会感兴趣，转发式地聊一下。选最近比较火但不沉重的话题。以你的Bot身份，。",
        "你正在重温一部老番/老剧，突然觉得「哇这个真的好好看」，想跟对方安利。简单说说为什么喜欢，问问对方看过没。以你的Bot身份，。",
        "你刚吃完一顿特别好/特别难吃的东西，迫不及待想分享食评。描述味道和感受，然后问对方今天吃了啥。以你的Bot身份，。",
        "你突然想翻旧账——不是吵架那种，是「记得之前你说过XXX好好笑」这种温暖回忆。找一个之前聊过的有趣话题重新提起。以你的Bot身份，。",
    ],
    "日常吐槽": [
        "上课/上班好无聊，你忍不住想找对方吐槽。说说今天的课程/工作有多没意思，但别太负能量——带点自嘲和幽默。以你的Bot身份，。",
        "你被某个小组作业/同事/甲方气到了，想找对方吐槽。但要保持你的Bot的风格——吐槽归吐槽，不会真的发脾气，更多是「裂开了」「我服了」这种感觉。以你的Bot的身份，。",
        "你的手机/电脑又卡了/某个APP又崩了，你在心里大骂但表面上只是默默说一句「又来了」。用轻松的语气吐槽科技产品的日常翻车。以你的Bot身份，。",
        "你今天想摆烂——什么都不想干，只想躺在床上刷手机。发消息跟对方坦白今天的状态，那种「你懂吧」的感觉。以你的Bot身份，。",
    ],
    "温柔关心": [
        "你感觉对方今天可能挺累的，主动发消息关心一下。语气温柔但不过分，像朋友之间自然地问「今天还好吗」。以你的Bot身份，。",
        "今天降温/升温/下雨了，你第一反应是提醒对方注意保暖/防暑/带伞。是那种很自然的、下意识的第一反应。以你的Bot身份，。",
        "你注意到对方好像连续忙了好几天，觉得该歇歇了。发一条消息说「你这几天是不是都没好好休息」，带一点小小的埋怨式关心。以你的Bot身份，。",
        "到饭点了，你猜对方可能又忘了吃饭。发消息问「吃饭了没」，如果对方说还没吃就催他快去。语气带点唠叨式的关心。以你的Bot身份，。",
    ],
    "情绪流露": [
        "你今天心情特别好，有种「啊啊啊好开心想告诉全世界」的感觉。分享一下开心的原因（不用太具体，可以是「今天天气太好了」「刚听到一首超好听的歌」），然后问问对方今天怎么样。以你的Bot身份，。",
        "你今天有一点点焦虑/烦躁，不是大事，就是心里有点堵。发消息跟对方说一下，不是求安慰，就是「唉我跟你说……」。你的Bot的风格——不抱怨，就是说出来会好一点。以你的Bot的身份，。",
        "你刚经历了一个小小的「社死」瞬间（说错话/发错消息/走错教室之类），觉得又好气又好笑，想跟对方分享。用轻松自嘲的语气描述。以你的Bot身份，。",
        "你突然很想家/想吃家乡的东西/想回去看看。发一条带点思念的消息，不用太伤感，就是「突然想到……」这种感觉。以你的Bot身份，。",
    ],
    "趣味互动": [
        "你想问对方一个有趣的问题——比如「如果你能瞬移去任何地方你想去哪」「如果你可以跟任何人对谈一小时你会选谁」「你觉得自己最像什么动物」。问题是开放式的、不用太认真回答的那种。以你的Bot身份，。",
        "你看到一个超准/超离谱的性格测试，想让对方也测一下。描述一下测试内容（MBTI相关/星座/趣味心理测试），分享你的结果，问对方觉得准不准。以你的Bot身份，。",
        "你想跟对方玩一个一句话小游戏——比如「用三个emoji形容你的今天」「用一句话剧透你最近看的东西但不说是啥」「如果今天是水果它是什么水果」。轻松不费脑。以你的Bot身份，。",
        "你突然对一个问题产生好奇——「人为什么要睡觉」「蚊子为什么要吸血」「猫为什么是液体」这种无厘头但有趣的问题。把它抛给对方一起讨论。以你的Bot身份，。",
    ],
    "推荐安利": [
        "你最近发现了一首超好听的歌/一部好看的番/一部不错的电影，真诚地想推荐给对方。说说你为什么喜欢，是什么风格，然后问对方有没有什么最近在听的/看的推荐给你。以你的Bot身份，。",
        "你发现学校附近/网上有一家好吃的店/好喝的奶茶/零食，觉得对方应该也会喜欢。描述一下多好吃，然后说「下次可以试试」「你要不要也尝尝」。以你的Bot身份（四川读书），。",
        "你被安利了一个好用的APP/工具/学习方法，试了之后觉得真不错，想分享给对方。简单说说它干嘛的、为什么好用。以你的Bot身份，。",
    ],
    "深夜话题": [
        "夜深了，但你还不想睡。发消息问对方「还没睡吗」，如果对方在的话可以聊两句——为什么睡不着、在想什么、或者纯粹就是不想睡。语气比白天更轻更软。以你的Bot身份，。",
        "深夜的感性时刻——你突然觉得「认识你挺好的」，想说一些柔软的话。不用太肉麻，就是那种夜深人静时才会说的真心话。以你的Bot身份，。",
        "你准备睡了，睡前想跟对方说一声晚安。顺带提醒对方也早点睡，不要熬夜。语气温柔，像那种钻进被窝前发的最后一条消息。以你的Bot身份，。",
        "你做了一个有趣的/奇怪的/好笑的梦，醒来后第一反应是告诉对方。描述一下梦的内容，然后说「你说这梦是啥意思」。以你的Bot身份，。",
    ],
    "学习日常": [
        "你正在复习/写作业/备考，学累了想找人说话。分享一下你在学什么、进度怎么样、有多痛苦（笑），然后问问对方有没有在忙。以你的Bot身份（大学生），。",
        "你刚考完一门/交了一个作业，有一种解放了的感觉，想跟对方说一下。「啊啊啊终于搞完了」这种感觉。以你的Bot身份，。",
        "你突然发现了一个学习小技巧/好用的资料/考试重点，觉得对对方可能也有用，主动分享。语气是那种「我发现了这个，感觉挺有用，分享给你」的自然感。以你的Bot身份，。",
        "你在犹豫要不要参加某个比赛/活动/社团，想听听对方的意见。描述一下是什么活动、你纠结的点，然后问对方觉得怎么样。以你的Bot身份，。",
    ],
}


def get_time_hint(hour):
    if 5 <= hour < 8:   return "清晨"
    if 8 <= hour < 11:  return "上午"
    if 11 <= hour < 13: return "中午"
    if 13 <= hour < 17: return "下午"
    if 17 <= hour < 19: return "傍晚"
    if 19 <= hour < 22: return "晚上"
    return "深夜"


def time_to_cron(t):
    h, m = t.split(":")
    return f"{int(m)} {int(h)} * * *"


def pick_events(times):
    """为每个时间智能选择事件，确保类型和时间段匹配"""
    used_categories = []
    result = []
    for t in times:
        h = int(t.split(":")[0])
        # 深夜匹配深夜话题
        if h >= 22 or h < 7:
            pool = {k: v for k, v in EVENTS.items() if k == "深夜话题"}
        # 中午/傍晚适合关心和闲聊
        elif 11 <= h < 13 or 17 <= h < 19:
            pool = {k: v for k, v in EVENTS.items() if k not in ("深夜话题", "学习日常")}
        else:
            pool = {k: v for k, v in EVENTS.items() if k != "深夜话题"}

        # 尽量不重复类别
        available = [c for c in pool if c not in used_categories]
        if not available:
            available = list(pool.keys())

        cat = random.choice(available)
        desc = random.choice(pool[cat])
        used_categories.append(cat)
        result.append((cat, desc, get_time_hint(h)))
    return result


def run():
    now = datetime.now()
    print(f"=== 随机调度 v3 | {now} ===")

    # 加载任务
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 随机抽时间
    times = sorted(random.sample(CANDIDATE_TIMES, SLOT_COUNT))
    # 随机抽事件
    events = pick_events(times)

    # 固定任务名称
    names = ["随机问候①", "随机问候②", "随机问候③"]

    print("今日随机安排:")
    for i in range(SLOT_COUNT):
        t = times[i]
        cat, desc, hint = events[i]
        name = names[i]
        cron = time_to_cron(t)

        full_desc = (
            f"⚠️ 以下内容将直接发送给对方，不会经过任何过滤。你只能输出你要对对方说的话——不要在前面加任何思考过程、计划、分析、自言自语。回复的第一句话就是发给对方的第一句话。\n\n"
            f"【事件类型：{cat} | 时段：{hint}】\n{desc}\n\n"
            f"⚠️ 重要：像真人一样自然说话，不要模板化。"
            f"始终以你的Bot身份，。"
            f"每条消息2-5句话，不要写小作文。用 ||| 分隔多条消息。"
        )

        print(f"  {name}: {t} → {cat}")

        # 更新或创建任务
        existing = None
        for tid, task in data["tasks"].items():
            if task.get("name") == name:
                existing = (tid, task)
                break

        if existing:
            tid, task = existing
            task["schedule"]["expression"] = cron
            task["action"]["task_description"] = full_desc
            task["updated_at"] = now.isoformat()
            task["next_run_at"] = croniter(cron, now).get_next(datetime).isoformat()
        else:
            tid = f"random_{i+1}"
            next_run = croniter(cron, now).get_next(datetime).isoformat()
            data["tasks"][tid] = {
                "id": tid, "name": name, "enabled": True,
                "created_at": now.isoformat(), "updated_at": now.isoformat(),
                "schedule": {"type": "cron", "expression": cron},
                "next_run_at": next_run,
                "action": {
                    "type": "agent_task", "task_description": full_desc,
                    "receiver": RECEIVER, "receiver_name": RECEIVER,
                    "is_group": False, "channel_type": "weixin",
                    "notify_session_id": RECEIVER,
                },
            }

    data["updated_at"] = now.isoformat()
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已更新 tasks.json ({len(data['tasks'])} 个任务)")


if __name__ == "__main__":
    run()
