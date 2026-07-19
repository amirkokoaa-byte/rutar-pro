import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hybrid_connection_engine import HybridConnectionEngine
from router_actions_executor import RouterActionsExecutor
from router_manager import RouterManager
from scapy.all import ARP, Ether, srp

from bandwidth_daemon import BandwidthDaemon
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Router Admin Local API", version="1.0")

# Global daemon instance
daemon = BandwidthDaemon(router_executor=None, flush_interval=10)
daemon.start()

# تفعيل CORS للسماح لتطبيق Vercel بالاتصال
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج، يفضل وضع رابط Vercel هنا
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for incoming requests
class LoginRequest(BaseModel):
    ip: str
    username: str
    password: str
    router_id: str

class WifiRequest(BaseModel):
    ip: str
    username: str
    password: str
    router_id: str
    ssid: str = None
    password_wifi: str = None
    hidden: bool = None

class LimitRequest(BaseModel):
    ip: str
    username: str
    password: str
    router_id: str
    mac_address: str
    speed_limit: int = None
    quota: float = None

@app.get("/api/devices")
def get_devices(network_cidr: str = "192.168.1.0/24"):
    """
    يجلب الأجهزة المتصلة بالشبكة باستخدام ARP scan عبر مكتبة Scapy
    """
    logging.info(f"Scanning network {network_cidr} using Scapy...")
    try:
        # إنشاء حزمة ARP
        arp = ARP(pdst=network_cidr)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        # إرسال الحزمة واستقبال الردود
        result = srp(packet, timeout=3, verbose=0)[0]
        
        devices = []
        for sent, received in result:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})
            
        return {"status": "success", "devices": devices}
    except Exception as e:
        logging.error(f"Scapy scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wifi")
def update_wifi(req: WifiRequest):
    """
    تغيير إعدادات الواي فاي باستخدام HybridConnectionEngine و RouterActionsExecutor
    """
    try:
        engine = HybridConnectionEngine(req.ip, req.username, req.password)
        session = engine.connect(req.router_id)
        if not session:
            raise HTTPException(status_code=401, detail="فشل تسجيل الدخول للراوتر.")
            
        executor = RouterActionsExecutor(req.ip, session, req.router_id)
        
        if req.ssid:
            executor.change_ssid(req.ssid)
        if req.password_wifi:
            executor.change_wlan_password(req.password_wifi)
        
        success = True
        
        engine._cleanup_playwright()
        
        if success:
            return {"status": "success", "message": "تم تحديث إعدادات الواي فاي بنجاح."}
        else:
            raise HTTPException(status_code=500, detail="لم يتمكن النظام من تحديث الإعدادات.")
            
    except Exception as e:
        logging.error(f"Error in /api/wifi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/limit")
def limit_speed(req: LimitRequest):
    """
    تحديد السرعة لجهاز معين أو تحديد حصة (Quota)
    """
    try:
        engine = HybridConnectionEngine(req.ip, req.username, req.password)
        session = engine.connect(req.router_id)
        if not session:
            raise HTTPException(status_code=401, detail="فشل تسجيل الدخول للراوتر.")
            
        executor = RouterActionsExecutor(req.ip, session, req.router_id)
        
        # update the daemon's executor so it can block devices when quota is reached
        daemon.router_executor = executor
        
        if req.speed_limit:
            router = RouterManager(req.ip, req.username, req.password)
            router.login()
            router.set_qos_limit(req.mac_address, req.speed_limit)
            router.stop_browser()
            
        if req.quota:
            daemon.set_quota(req.mac_address, req.quota)
            
        # Do not cleanup if daemon is running, wait, daemon needs executor
        # We might need to keep the session alive, but for now we just return
        
        return {"status": "success", "message": f"تم تطبيق القيود بنجاح على الماك {req.mac_address}"}
        
    except Exception as e:
        logging.error(f"Error in /api/limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # الخادم يعمل محلياً ويستمع على كل الواجهات
    uvicorn.run(app, host="0.0.0.0", port=3000)
