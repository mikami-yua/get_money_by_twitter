# get_money_by_twitter

# 高可用Twitter关键词监控与通知机器人

一个能7x24小时自动监控Twitter，精准捕捉“口令红包”、“Web3空投”等时效性信息，并通过邮件实时告警的智能机器人。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ 项目亮点 (Key Features)

* **高可用架构:** 支持多账号自动轮换，单个账号因API限制或失效后，系统会自动切换到下一个健康账号，确保监控任务不中断。
* **智能健康检测:** 具备账号健康状态监控能力，当某个账号连续多次请求失败时，会自动禁用该账号并向管理员发送邮件告警。
* **三维高精度过滤:**
    1.  **服务器端过滤:** 通过高度定制化的查询语句，在API层面过滤掉绝大多数噪音。
    2.  **客户端时效性过滤:** 独创`start_time`机制，确保每一条被处理的推文都具备极高的时效性，最大化利用API配额。
    3.  **客户端内容过滤:** 强大的、可扩展的正则表达式解析器，精准提取目标信息。
* **健壮的容错机制:**
    * 邮件发送模块内置重试逻辑，从容应对瞬时网络抖动。
    * 主程序具备完善的异常捕获，避免因意外错误而崩溃。
* **完善的单元测试:** 配备独立的单元测试模块，可在不消耗API配额的情况下，对核心解析逻辑和通知功能进行验证和迭代。
* **低成本部署:** 专为在低成本云服务器（VPS）上长期运行而设计。

## 🚀 工作流程

本机器人采用“低频轮换、高精度打击”的策略，其工作流程如下：

1.  **轮换唤醒:** `main.py` 作为总司令，按预设时间间隔（例如3分钟），唤醒一个健康的Twitter账号。
2.  **精准索敌:** 使用`config.py`中定义的“神级”查询语句，通过`start_time`机制向Twitter请求一个极小时间窗口内的、高度相关的推文。
3.  **情报分析:** `parser.py` 作为情报分析官，对获取到的推文进行“火眼金睛”般的正则匹配，提取出口令等核心信息。
4.  **即时告警:** 如果发现目标，`notifier.py` 作为通信兵，立刻将战报（口令、推文链接等）通过邮件发送给管理员。
5.  **健康上报:** 如果某个账号连续阵亡（请求失败），系统会自动发送告警邮件，并将其标记为“伤员”，不再派遣任务。
6.  **休眠待命:** 完成本轮任务后，机器人进入休眠，等待下一次唤醒。

## 🔧 开始使用 (Getting Started)

### 1. 先决条件

* Python 3.9 或更高版本
* 一个或多个Twitter开发者账号及对应的API密钥
* 一个用于发送通知的Gmail邮箱及对应的**应用专用密码**

### 2. 安装步骤

1.  **克隆或下载项目到你的服务器或本地电脑**
    ```bash
    git clone https://github.com/mikami-yua/get_money_by_twitter.git
    cd get_money_by_twitter
    ```

2.  **安装依赖**
    ```bash
    pip3 install -r requirements.txt
    ```

3.  **创建并配置 `config.py`**
    * 将 `config.py`或根据下面的模板，创建一个名为 `config.py` 的文件。
    * 填入你所有的Twitter账号API密钥和Gmail配置。
    ```python
    # config.py
    ACCOUNTS = [
        {
            "name": "Account 1",
            "emailid": "account1@example.com",
            "api_key": "...", 
            "api_secret": "...",
            "access_token": "...", 
            "access_token_secret": "...",
            "bearer_token": "..."
        },
        # ... 在此添加更多账号 ...
    ]
    SEARCH_QUERY = '(口令红包 OR 支付宝口令) ("口令是" OR "密码是" OR "送个") ...'
    POLLING_INTERVAL_SECONDS = 180 # 3分钟
    EMAIL_CONFIG = {
        "use_email": True,
        "smtp_server": "smtp.gmail.com",
        "port": 465,
        "sender_email": "...",
        "password": "...", # 16位Gmail应用专用密码
        "receiver_email": "..."
    }
    ```

### 3. 使用方法

1.  **运行单元测试 (推荐)**
    * 在部署前，先运行单元测试确保所有模块工作正常。
    * 编辑 `unit_test.py` 顶部的开关，选择要测试的功能。
    ```bash
    python3 unit_test.py
    ```

2.  **正式运行主程序**
    ```bash
    python3 main.py
    ```

3.  **在服务器后台长期运行 (推荐)**
    * 使用 `screen` 或 `tmux` 工具来确保程序在你断开SSH连接后依然运行。
    ```bash
    # 启动一个名为 "robot" 的新screen会话
    screen -S robot

    # 在新会话中，运行你的程序
    python3 main.py

    # 按下 Ctrl+A 然后按 D，即可从会话中分离，程序会继续在后台运行
    # 想再次连接时，使用 screen -r robot
    ```

## 📂 模块说明

* `main.py`: 项目主入口和总调度中心，负责主循环和调用其他模块。
* `config.py`: 存放所有配置信息，包括API密钥、搜索词、邮箱设置等。
* `parser.py`: 核心解析器，负责从推文文本中提取目标信息。
* `notifier.py`: 通知模块，负责发送邮件告警。
* `run_tests.py`: 统一的单元测试运行器，用于在本地验证模块功能。
* `requirements.txt`: 项目的Python依赖库列表。

## 🗺️ 未来路线图 (Roadmap)

* [ ] **拓展监控领域:** 增加对Web3空投、白名单等信息的关键词规则。
* [ ] **拓展监控平台:** 探索将此框架适配到其他社交平台（如微博）的可能性。
* [ ] **优化通知渠道:** 增加对Telegram Bot、Discord Webhook等其他通知方式的支持。

## 📜 许可证 (License)

本项目采用 [MIT License](LICENSE) 开源许可证。