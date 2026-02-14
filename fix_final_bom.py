path = r"E:\SHAD\GROTA_LUMENA\CORE\corex\socket_manager.py"
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("BOM Stripped via utf-8-sig reading.")
