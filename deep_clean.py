import os
path = r"E:\SHAD\GROTA_LUMENA\CORE\corex\socket_manager.py"
with open(path, 'rb') as f:
    raw = f.read()

# Remove anything before the first "import" or "from"
import_index = raw.find(b'import')
from_index = raw.find(b'from')
start = min(i for i in [import_index, from_index] if i >= 0)

clean_content = raw[start:]
with open(path, 'wb') as f:
    f.write(clean_content)
print(f"Deep cleaned: {path}")
