import os
def strip_bom(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    if content.startswith(b'\xef\xbb\xbf'):
        with open(file_path, 'wb') as f:
            f.write(content[3:])
        return True
    return False

root = r"E:\SHAD\GROTA_LUMENA\CORE\corex"
for f in os.listdir(root):
    if f.endswith(".py"):
        full = os.path.join(root, f)
        if strip_bom(full):
            print(f"CLEANED: {full}")
