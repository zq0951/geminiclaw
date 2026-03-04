#!/usr/bin/env python3
import json
import sys
import datetime

def get_system_status():
    """Retrieve system CPU, Memory and Disk utilization."""
    status = {
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "partial"
    }
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status.update({
            "status": "full",
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": disk.percent
            }
        })
    except ImportError:
        status.update({
            "status": "degraded",
            "message": "Python module 'psutil' not found. Please run 'pip install psutil' for full system stats.",
            "cpu_percent": None,
            "memory": {"total_gb": None, "used_gb": None, "percent": None},
            "disk": {"total_gb": None, "used_gb": None, "percent": None}
        })
    except Exception as e:
        status.update({
            "status": "error",
            "message": str(e)
        })
        
    return status

if __name__ == "__main__":
    status = get_system_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
