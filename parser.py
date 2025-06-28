import re


def extract_password(tweet_text: str) -> str | None:
    """
    使用一系列正则表达式，按顺序从推文文本中提取口令。

    Args:
        tweet_text (str): 从Twitter获取到的原始推文内容。

    Returns:
        str | None: 如果成功提取到口令，则返回该口令字符串；否则返回None。
    """
    # 预处理：移除全角冒号和空格，方便正则匹配
    # 并将文本转为小写，以忽略大小写差异（比如 "Password:" vs "password:"）
    processed_text = tweet_text.replace('：', ':').replace(' ', '').lower()

    # --- 正则表达式规则列表 ---
    # 定义一个元组列表，每个元组包含 (规则描述, 正则表达式)
    # 我们将按列表顺序进行匹配，一旦成功，立即返回结果。
    # [a-z0-9]+ 匹配一个或多个小写字母或数字
    patterns = [
        # --- 高优先级规则 (最可能精确匹配) ---
        ("冒号引导词", r'(?:口令是|口令|password):([a-z0-9]+)'),
        ("支付宝引导词", r'支付宝:([a-z0-9]+)'),
        ("括号/引号引导", r'(?:口令|密码)[「（【]([a-z0-9]+)[」）】]'),

        # --- 中优先级规则 (可能会误判，但值得一试) ---
        # 匹配被空格、换行符或特定词包围的长数字串，假设口令至少8位
        ("纯数字长口令", r'^\b(\d{8,})\b$'),  # 整条推文就是一串8位以上的数字
        ("被特定词包围的数字", r'(?:送个|发个|来个|一个)(\d{8,})'),

        # --- 低优先级规则 (补充) ---
        # 可以在这里添加更多你观察到的、不常见的格式
    ]

    print(f"\n--- 正在解析文本: '{tweet_text[:30]}...'")  # 打印前30个字符用于调试
    for description, pattern in patterns:
        match = re.search(pattern, processed_text)
        if match:
            # group(1) 返回正则表达式中第一个括号 () 内捕获的内容
            password = match.group(1)
            print(f"    ✅ 匹配成功! 规则: '{description}', 结果: '{password}'")
            return password

    # 如果所有规则都未匹配成功
    print("    🤷 所有规则均未匹配成功。")
    return None