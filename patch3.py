with open('src/core/client.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace GUI status updates containing 'idle'
s_old = 'self.gui.status.update(_.t["gui"]["status"]["idle"])'
s_new = 'self.gui.status.update("Mining...")'
code = code.replace(s_old, s_new)

with open('src/core/client.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patched GUI idle status in client.py")
