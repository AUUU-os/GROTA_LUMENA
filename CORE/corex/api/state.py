from typing import Optional
from corex.daemon import CoreXDaemon

# Global references to avoid circular imports
daemon: Optional[CoreXDaemon] = None
