files = [
    r"E:\SHAD\GROTA_LUMENA\CORE\corex\socket_manager.py",
    r"E:\SHAD\GROTA_LUMENA\CORE\corex\api_server.py",
    r"E:\SHAD\GROTA_LUMENA\CORE\corex\neural_sync.py"
]
for path in files:
    with open(path, 'rb') as f:
        content = f.read()
    if content.startswith(b'\xef\xbb\xbf'):
        with open(path, 'wb') as f:
            f.write(content[3:])
        print(f"BOM removed: {path}")
