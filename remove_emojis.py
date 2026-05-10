import re

def remove_emojis(text):
    # Regex to match emojis and other pictographs
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27FF]', '', text)

with open('frontend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = remove_emojis(content)
# Clean up some common emoji-related artifacts like extra spaces
content = content.replace('  ', ' ')

with open('frontend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
