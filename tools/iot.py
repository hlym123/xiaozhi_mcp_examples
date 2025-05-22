from mcp.server.fastmcp import FastMCP
import sys
import logging
import json
import paho.mqtt.client as mqtt
import threading
import time
from typing import Dict, Optional


logger = logging.getLogger('MCP-IoT')


latest_data = {
    "temperature": None,
    "humidity": None,
}

class MQTTController:
    def __init__(self):
        self.client = None
        self.lock = threading.Lock()
        self.connected = False
        
    def initialize(self):
        with self.lock:
            if self.client is None:
                self.client = mqtt.Client()
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                self.client.on_message = self._on_message 
                try:
                    self.client.connect("test.mosquitto.org", 1883, 60)
                    #self.client.connect("broker-cn.emqx.io", 1883, 60) # 选择连接的 MQTT 服务器
                    self.client.loop_start()
                    for _ in range(10):
                        if self.connected:
                            return True
                        time.sleep(0.5)
                    return False
                except Exception as e:
                    logger.error(f"MQTT初始化失败: {e}")
                    return False
            return self.connected

    def _on_connect(self, client, userdata, flags, rc):
        with self.lock:
            self.connected = True
            logger.info(f"MQTT连接成功，代码: {rc}")
            client.subscribe("esp32/temphumi")

    def _on_disconnect(self, client, userdata, rc):
        with self.lock:
            self.connected = False
            logger.warning(f"MQTT断开连接，代码: {rc}")
            self._attempt_reconnect()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        if topic == "esp32/temphumi":
            try:
                data = json.loads(payload)
                if "temperature" in data and "humidity" in data:
                    latest_data["temperature"] = float(data["temperature"])
                    latest_data["humidity"] = float(data["humidity"])
                    logger.info(f"接收到温湿度数据: T={data['temperature']} H={data['humidity']}")
            except Exception as e:
                logger.warning(f"解析温湿度数据失败: {e}")

    def _attempt_reconnect(self):
        def reconnect_task():
            while not self.connected:
                try:
                    logger.info("尝试重新连接MQTT...")
                    self.client.reconnect()
                    time.sleep(5)  # 重连间隔
                except Exception as e:
                    logger.error(f"重连失败: {e}")
                    time.sleep(10)
                    
        threading.Thread(target=reconnect_task, daemon=True).start()

    def publish(self, topic: str, payload: str) -> bool:
        with self.lock:
            if not self.connected:
                logger.error("发布失败：MQTT未连接")
                return False
            try:
                result = self.client.publish(topic, payload, qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    return True
                logger.error(f"发布错误代码: {result.rc}")
                return False
            except Exception as e:
                logger.error(f"发布异常: {e}")
                return False

mqtt_controller = MQTTController()
mqtt_controller.initialize()

def register_iot_tools(mcp: FastMCP):
    @mcp.tool()
    def set_rgb(r: int, g: int, b: int) -> Dict:
        """
        设置 RGB 彩灯颜色。

        参数：
            r: 红色亮度（0-255）
            g: 绿色亮度（0-255）
            b: 蓝色亮度（0-255）

        功能：
            将指定颜色通过 MQTT 发布给 ESP32，使其控制 RGB LED 发出对应颜色。

        返回值：
            成功或失败的状态及提示信息。

        MQTT 主题（ESP32 端需订阅）：
            esp32/rgbled
            消息格式示例：
                关灯 {"r": 0, "g": 0, "b": 0}
                开灯 {"r": 50, "g": 50, "b": 50}
                
        """
        if not mqtt_controller.initialize():
            return {"success": False, "error": "MQTT连接不可用"}
            
        if not all(0 <= x <= 255 for x in (r, g, b)):
            return {"success": False, "error": "RGB值必须在0-255之间"}
            
        payload = json.dumps({"r": r, "g": g, "b": b})
        if mqtt_controller.publish("esp32/rgbled", payload):
            return {"success": True, "message": f"颜色设置为({r},{g},{b})"}
        return {"success": False, "error": "MQTT发布失败"}

    @mcp.tool()
    def set_fan(speed: int) -> Dict:
        """
        设置风扇转速。

        参数：
            speed: 风扇速度（0~100），0 表示关闭，100 表示最大转速。

        MQTT 主题（ESP32 端需订阅）：
            esp32/fan
            消息格式示例：
                {"speed": 0}   -> 关风扇
                {"speed": 50}  -> 中速
                {"speed": 100} -> 全速
        """
        if not mqtt_controller.initialize():
            return {"success": False, "error": "MQTT连接不可用"}
            
        if not 0 <= speed <= 100:
            return {"success": False, "error": "转速必须在0-100之间"}
            
        payload = json.dumps({"speed": speed})
        if mqtt_controller.publish("esp32/fan", payload):
            return {"success": True, "message": f"风扇转速设置为{speed}%"}
        return {"success": False, "error": "MQTT发布失败"}

    @mcp.tool()
    def get_temphum() -> dict:
        """
        获取温湿度数据。
        返回示例：
        {
            "success": True,
            "temperature": 25.5,
            "humidity": 60.2
        }
        """
        if latest_data["temperature"] is None or latest_data["humidity"] is None:
            return {"success": False, "error": "No data received yet."}
        return {
            "success": True,
            "temperature": latest_data["temperature"],
            "humidity": latest_data["humidity"]
        }
