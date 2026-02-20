import os
import re

prompts_dir = r"c:\investment advisor\prompts"

# 1. Update Gold & Silver (1A, 1B, 1C)
for f in ["1A - Gold & Silver News Agent.txt", "1B - Gold & Silver Market & Fundamental Agent.txt", "1C - Gold & Silver Social & Sentiment Agent.txt"]:
    path = os.path.join(prompts_dir, f)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        content = content.replace("REPORT_2", "REPORT_1")
        content = content.replace("2A", "1A").replace("2B", "1B").replace("2C", "1C")
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

# 2. Update Global Stocks & Funds (2A, 2B, 2C)
for f in ["2A - Global Stocks & Funds News Agent.txt", "2B - Global Stocks & Funds Market & Fundamental Agent.txt", "2C - Global Stocks & Funds Social & Sentiment Agent.txt"]:
    path = os.path.join(prompts_dir, f)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        content = re.sub(r"- THYAO \(BIST\)\n*", "", content)
        content = re.sub(r"- TUPRS \(BIST\)\n*", "", content)
        content = re.sub(r"- ENJSA \(BIST\)\n*", "", content)
        content = re.sub(r"- ASELS \(BIST\)\n*", "", content)
        content = re.sub(r"- BIMAS \(BIST\)\n*", "", content)
        content = content.replace("STOCKS & FUNDS", "GLOBAL STOCKS & FUNDS")
        content = content.replace("REPORT_3A", "REPORT_2A").replace("REPORT_3B", "REPORT_2B").replace("REPORT_3C", "REPORT_2C")
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

# 3. Update Turkish Stocks & Funds (3A, 3B, 3C)
for f in ["3A - Turkish Stocks & Funds News Agent.txt", "3B - Turkish Stocks & Funds Market & Fundamental Agent.txt", "3C - Turkish Stocks & Funds Social & Sentiment Agent.txt"]:
    path = os.path.join(prompts_dir, f)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        content = re.sub(r"- ASML \(NASDAQ\)\n*", "", content)
        content = re.sub(r"FUNDS / ETFs:.*?\n- HLAL\n- SPUS\n*", "", content, flags=re.DOTALL)
        content = content.replace("STOCKS & FUNDS", "TURKISH STOCKS & FUNDS")
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

print("Prompts updated successfully!")
