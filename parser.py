# twitter_bot/parser.py
import re


def extract_password(tweet_text: str) -> str | None:
    """
    使用一系列正则表达式，按顺序从推文文本中提取口令。
    """
    # 预处理：只替换全角冒号，暂时保留空格，让正则处理
    processed_text = tweet_text.replace('：', ':').lower()

    # --- 正则表达式规则列表 (v5 修复版 - 处理URL污染问题) ---
    # !! 核心改动：使用非贪婪匹配和先行断言来界定密码边界 !!
    patterns = [
        ("固定引导词+冒号", r'(?:口令是|口令|password)\s*:\s*([a-z0-9_\u4e00-\u9fa5]+?)(?=[^a-z0-9_\u4e00-\u9fa5]|$)'),
        ("支付宝引导词+冒号", r'支付宝\s*:\s*([a-z0-9_\u4e00-\u9fa5]+?)(?=[^a-z0-9_\u4e00-\u9fa5]|$)'),
        ("括号/引号引导", r'(?:口令|密码)\s*[「（【]\s*([a-z0-9_\u4e00-\u9fa5]+?)\s*[」）】]'),
        ("关键词+冒号", r'口令红包.*?\s*[:]\s*([a-z0-9_\u4e00-\u9fa5]+?)(?=[^a-z0-9_\u4e00-\u9fa5]|$)'),
        ("关键词紧邻数字", r'支付宝口令红包\s*(\d{6,})'),
        ("纯数字长口令", r'^\s*(\d{8,})\s*$'),
    ]

    print(f"\n--- 正在解析文本: '{tweet_text[:40]}...'")
    for description, pattern in patterns:
        match = re.search(pattern, processed_text)
        if match:
            # group(1) 仍然是我们的目标
            password = match.group(1).strip()  # strip() 移除可能捕获到的前后空格
            if password in ["红包", "私信", "已发"]:
                continue
            print(f"    ✅ 匹配成功! 规则: '{description}', 结果: '{password}'")
            return password

    print("    🤷 所有规则均未匹配成功。")
    return None