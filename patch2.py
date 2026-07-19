import sys
import re

with open('src/core/client.py', 'r', encoding='utf-8') as f:
    code = f.read()

s_old1 = 'self.print(_.t["status"]["no_campaign"])'
s_new1 = 'self.print("Mining...")'
code = code.replace(s_old1, s_new1)

s_old2 = 'self.print(_.t["status"]["no_channel"])'
code = code.replace(s_old2, s_new1)

with open('src/core/client.py', 'w', encoding='utf-8') as f:
    f.write(code)

with open('src/services/watch_service.py', 'r', encoding='utf-8') as f:
    ws_code = f.read()

s_old3 = 'save_runtime_status(DATA_DIR, _.t["gui"]["status"]["idle"])'
s_new3 = 'save_runtime_status(DATA_DIR, "Mining...")'
ws_code = ws_code.replace(s_old3, s_new3)

with open('src/services/watch_service.py', 'w', encoding='utf-8') as f:
    f.write(ws_code)

print("SUCCESS")
