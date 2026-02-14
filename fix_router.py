path = r"E:\SHAD\GROTA_LUMENA\CORE\corex\swarm\router.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('router = APIRouter(prefix="/api/v1/swarm", tags=["Swarm Nexus"])', 'router = APIRouter(tags=["Swarm Nexus"])')
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Router prefix removed.")
