# 🤖 CowBot — 微信 AI Bot 模板

一键部署属于你自己的微信 AI Bot。支持自定义人设、情绪化表情包、定时主动消息。

基于 [CowAgent](https://github.com/chenhg5/CowAgent) + [cc-connect](https://github.com/chenhg5/cc-connect)，用 Markdown 文件管理人设，零代码定制。

## 能做什么

- 💬 **像真人一样聊天**：短句、吐槽、表情包——不是客服机器人
- 😤 **按情绪发图**：12 种情绪文件夹，Bot 自动匹配
- ⏰ **主动发消息**：早安晚安、随机互动，cron 定时触发
- ✂️ **多消息分段**：长回复自动拆成多条发送
- 🎲 **每天不重样**：随机事件调度器，30+ 种场景每天随机组合
- 🛡️ **防呆**：不存在的图片静默跳过，不发错误提示

## 架构

```
微信 → cc-connect → CowAgent → DeepSeek / Claude / OpenAI
                      │
                CLAUDE.md   ← 你只改这个文件就能定制人设
                表情包/      ← 按情绪放图片
                scheduler/   ← 定时任务配置
```

## 5 分钟上手

### 1. 装依赖

```bash
npm install -g cc-connect          # 微信桥接
git clone https://github.com/chenhg5/CowAgent.git
cd CowAgent && pip install -r requirements.txt && pip install croniter
```

### 2. 配 Bot

```bash
cp config.example.toml config.toml
```

编辑 `config.toml`，填三个东西：

```toml
ANTHROPIC_AUTH_TOKEN = "sk-xxx"           # DeepSeek 或 Anthropic API Key
token = "xxx@im.bot:xxx"                  # 微信 Bot Token
account_id = "xxx@im.bot"                 # 微信 Bot 账号 ID
```

### 3. 定人设

编辑 `CLAUDE.md`，告诉 Bot 它是谁。20 行就能写完：

```markdown
你是「小助手」，一个温柔的朋友。

## 说话的样子
短句、自然、像真人。emoji 只用 🐶 🌹 💩 😢 😭 😫 😜 🥀 👌。

## 性格
开朗、随和、偶尔吐槽。
```

### 4. 启动

```bash
cc-connect --config config.toml &
cd CowAgent && python app.py
```

扫码登录微信，Bot 上线。

## 高级功能

### 表情包系统

在 `表情包/` 下按情绪放图片，Bot 聊天时自动引用：

```
[图片: 表情包/搞怪整活/大笑.png]
```

12 个情绪文件夹已建好，放入图片即用。Bot 只引用真实存在的文件，不会编造路径。

### 定时主动消息

编辑 `scheduler/tasks.example.json` → 重命名为 `tasks.json`：

```json
{
  "morning": {
    "id": "morning",
    "name": "早安",
    "enabled": true,
    "schedule": {"type": "cron", "expression": "0 8 * * *"},
    "action": {
      "type": "agent_task",
      "task_description": "发早安问候，语气自然。2-3句。",
      "receiver": "对方微信ID",
      "channel_type": "weixin"
    }
  }
}
```

支持三种 action 类型：`agent_task`（AI 生成）、`send_message`（固定文本）、`tool_call`（执行工具）。

### 随机事件调度器

`scripts/random_event_scheduler.py`：30+ 种事件预设，每天凌晨自动抽取 3 个时间 + 3 种场景，保证 Bot 主动消息每天不重样。

```bash
# 加到 cron，每天凌晨刷新
0 0 * * * python3 scripts/random_event_scheduler.py
```

## 目录结构

```
cow-bot-template/
├── CLAUDE.md                     # Bot 人设——改这个就够了
├── config.example.toml           # cc-connect 配置模板
├── README.md
├── .gitignore
├── 表情包/                       # 12 个情绪文件夹
│   ├── 生气气/    ├── 委屈巴巴/  ├── 温柔撒娇/
│   ├── 震惊崩溃/  ├── 摆烂躺平/  ├── 吐槽无语/
│   ├── 搞怪整活/  ├── 困了累了/  ├── 干饭time/
│   ├── 鼓励加油/  ├── 日常闲聊/  └── 不知道怎么回/
├── scheduler/
│   └── tasks.example.json        # 定时任务配置
├── scripts/
│   └── random_event_scheduler.py # 随机事件调度
└── cowagent-patches/             # CowAgent 增强补丁
    ├── weixin_channel.py         # ||| 分段 + 发图
    ├── chat_channel.py           # 路径解析 + 标记剥离
    └── integration.py            # 媒体提取 + 思考过滤
```

## CowAgent 增强补丁

`cowagent-patches/` 下的文件替换 CowAgent 对应文件，解锁全部功能：

| 文件 | 功能 |
|------|------|
| `weixin_channel.py` | `\|\|\|` 自动分条发送；图片路径解析 |
| `chat_channel.py` | `[图片: 路径]` 标记剥离 + 工作空间路径解析 |
| `integration.py` | 定时任务的媒体发送；思考前缀过滤 |

```bash
cp cowagent-patches/weixin_channel.py CowAgent/channel/weixin/
cp cowagent-patches/chat_channel.py CowAgent/channel/
cp cowagent-patches/integration.py CowAgent/agent/tools/scheduler/
```

## 识图（可选）

在 CowAgent `config.json` 中配置多模态模型即可启用识图：

```json
{
  "dashscope_api_key": "你的千问API Key",
  "tools": {"vision": {"model": "qwen-vl-plus"}}
}
```

用户发图后说「这是什么」，Bot 会自动调用 VL 模型识别。

## 部署到服务器

推荐 Ubuntu 云服务器 + systemd 守护：

```ini
# /etc/systemd/system/cowagent.service
[Service]
ExecStart=/usr/bin/python3 /root/CowAgent/app.py
Restart=always
```

```bash
systemctl enable --now cowagent
```

最低配置：1核1G，20GB 磁盘。腾讯云/阿里云新用户约 68-79 元/年。

## License

MIT — 随便改、随便用。
