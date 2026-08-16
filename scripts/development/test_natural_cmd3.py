import re

lower_tests = [
    'open chrome.',
    'launch chrome.',
    'can you open my browser?',
    'get chrome up.',
    'open my browser.',
    'could you open chrome?',
    'bring up firefox.',
    'load edge.',
]

def test_classify_request(text):
    lower = text.strip().lower()
    if any(phrase in lower for phrase in ["open ", "launch ", "start ", "run ", "find file", "create file", "create folder", "search file"]):
        return {"intent": "files", "confidence": 0.86}
    if any(phrase in lower for phrase in ["can you open", "could you open", "would you open", "open my", "open the"]):
        return {"intent": "files", "confidence": 0.8}
    if re.search(r"\b(get|bring up|load)\s+(chrome|firefox|edge|chrome browser|my browser)\b", lower):
        return {"intent": "files", "confidence": 0.85}
    match = re.search(r"^(?:open|launch|start|run|execute)\s+(?:my\s+|the\s+)?(.+?)(?:\s+for\s+me)?$", lower)
    if match:
        target = match.group(1).strip().rstrip('.!,')
        target = re.sub(r"\b(application|app|program|software)\b", "", target).strip()
        if target:
            return {"intent": "open_app", "target": target, "confidence": 1.0}
    if lower.startswith(("open file ", "open the file ", "open a file ")):
        target = re.sub(r"^(?:open\s+(?:the\s+|a\s+)?file\s+)", "", lower).strip()
        if target:
            return {"intent": "open_file", "target": target, "confidence": 0.9}
    if lower.startswith(("open folder ", "open the folder ", "open directory ", "show folder ")):
        target = re.sub(r"^(?:open\s+(?:the\s+)?(?:folder|directory)\s+)", "", lower).strip()
        if target:
            return {"intent": "open_folder", "target": target, "confidence": 0.9}
    if lower.startswith("show folder "):
        target = lower.replace("show folder ", "").strip()
        if target:
            return {"intent": "open_folder", "target": target, "confidence": 0.9}
    if re.search(r"can you open|could you open|would you open\s+my\s+\w+", lower):
        browser_match = re.search(r"(can you open|could you open|would you open)\s+my\s+(\w+)", lower)
        if browser_match:
            return {"intent": "open_app", "target": browser_match.group(2), "confidence": 0.95}
    if re.search(r"(can you open|could you open|would you open)\s+(\w+)", lower):
        open_match = re.search(r"(can you open|could you open|would you open)\s+(\w+)", lower)
        if open_match:
            return {"intent": "open_app", "target": open_match.group(2), "confidence": 0.9}
    if re.search(r"\b(get|bring up|load)\s+(chrome|firefox|edge|chrome browser|my browser)\b", lower):
        app_match = re.search(r"\b(get|bring up|load)\s+(\w+)", lower)
        if app_match:
            return {"intent": "open_app", "target": app_match.group(2), "confidence": 0.95}
        return {"intent": "open_app", "target": "chrome", "confidence": 0.9}
    if re.search(r"\bopen\s+(chrome|firefox|edge)\b", lower) or re.search(r"\blaunch\s+(chrome|firefox|edge)\b", lower):
        app_match = re.search(r"\b(open|launch)\s+([a-z]+)", lower)
        if app_match:
            target = re.sub(r"[.!,]$", "", app_match.group(2))
            return {"intent": "open_app", "target": target, "confidence": 0.98}
    return {"intent": "conversation", "confidence": 0.6}

print("=== Enhanced classify_request test ===")
for t in lower_tests:
    result = test_classify_request(t)
    print(f'  "{t}" -> {result}')

print()
def test_command_router_classify(text):
    lower = text.lower().strip()
    match = re.search(r"^(?:open|launch|start|run|execute)\s+(?:my\s+|the\s+)?(.+?)(?:\s+for\s+me)?$", lower)
    if match:
        target = match.group(1).strip().rstrip('.!,')
        target = re.sub(r"\b(application|app|program|software)\b", "", target).strip()
        if target:
            return {"intent": "open_app", "target": target, "confidence": 1.0}
    if re.search(r"can you open|could you open|would you open\s+my\s+\w+", lower):
        browser_match = re.search(r"(can you open|could you open|would you open)\s+my\s+(\w+)", lower)
        if browser_match:
            return {"intent": "open_app", "target": browser_match.group(2), "confidence": 0.95}
    if re.search(r"(can you open|could you open|would you open)\s+(\w+)", lower):
        open_match = re.search(r"(can you open|could you open|would you open)\s+(\w+)", lower)
        if open_match:
            return {"intent": "open_app", "target": open_match.group(2), "confidence": 0.9}
    if re.search(r"\b(get|bring up|load)\s+(chrome|firefox|edge|chrome browser|my browser)\b", lower):
        app_match = re.search(r"\b(get|bring up|load)\s+(\w+)", lower)
        if app_match:
            return {"intent": "open_app", "target": app_match.group(2), "confidence": 0.95}
        return {"intent": "open_app", "target": "chrome", "confidence": 0.9}
    if re.search(r"\bopen\s+(chrome|firefox|edge)\b", lower) or re.search(r"\blaunch\s+(chrome|firefox|edge)\b", lower):
        app_match = re.search(r"\b(open|launch)\s+([a-z]+)", lower)
        if app_match:
            target = re.sub(r"[.!,]$", "", app_match.group(2))
            return {"intent": "open_app", "target": target, "confidence": 0.98}
    return None

print("=== CommandRouter.classify test ===")
for t in lower_tests:
    result = test_command_router_classify(t)
    print(f'  "{t}" -> {result}')