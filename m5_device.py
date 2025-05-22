import network
import time
from umqtt.simple import MQTTClient
import machine
import json
import M5
from M5 import *
from unit import RGBUnit, ENVUnit
from hardware import I2C
from hardware import Pin



M5.begin()
Widgets.fillScreen(0)
title = Widgets.Title("IoT Control", 3, 0xFFFFFF, 0x0000FF, Widgets.FONTS.DejaVu24)
label_t = Widgets.Label("Temp:", 25, 55, 1.0, 0xFFFFFF, 0, Widgets.FONTS.DejaVu18)
label_h = Widgets.Label("Humi:", 25, 85, 1.0, 0xFFFFFF, 0, Widgets.FONTS.DejaVu18)
label_temp = Widgets.Label(" ", 90, 55, 1.0, 0xFFFFFF, 0, Widgets.FONTS.DejaVu18)
label_humi = Widgets.Label(" ", 90, 85, 1.0, 0xFFFFFF, 0, Widgets.FONTS.DejaVu18)


# Wi-Fi 配置
WIFI_SSID = 'LokiLab'
WIFI_PASSWORD = 'liang892983'

# MQTT 配置
mqtt_server = "test.mosquitto.org"
# mqtt_server = "broker-cn.emqx.io" # 选择连接的 MQTT 服务器
client_id = "esp32_rgbled"
topic_led = b'esp32/rgbled'      
topic_env = b'esp32/temphumi'     

# 初始化 RGB (M5CoreS3 PORT.B）
rgb_led = RGBUnit((8, 9), 72)
rgb_led.fill_color(0)

# 初始化 ENV (M5CoreS3 PORT.A）
i2c0 = I2C(0, scl=Pin(1), sda=Pin(2), freq=100000)
env_sensor = ENVUnit(i2c=i2c0, type=3)
 

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep_ms(100)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("WiFi connected:", wlan.ifconfig())

def set_color(r, g, b):
    color = (r << 16) | (g << 8) | b
    rgb_led.fill_color(color)

def sub_cb(topic, msg):
    print("MQTT Message:", topic, msg)
    try:
        data = json.loads(msg)
        r = int(data.get("r", 0))
        g = int(data.get("g", 0))
        b = int(data.get("b", 0))
        set_color(r, g, b)
    except Exception as e:
        print("Error parsing MQTT message:", e)

def publish_data(client):
    try:
        temp = env_sensor.read_temperature()
        humi = env_sensor.read_humidity()
        payload = json.dumps({
            "temperature": round(temp, 1),
            "humidity": round(humi, 1)
        })
        client.publish(topic_env, payload)
        print("Published:", payload)
    except Exception as e:
        print("Error reading sensor:", e)

def main():
    connect_wifi()
    client = MQTTClient(client_id, mqtt_server)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(topic_led)
    print("MQTT connected, listening on:", topic_led.decode())
    cnt = 0;
    last_time = time.ticks_ms()
    while True:
        client.check_msg()
        if time.ticks_diff(time.ticks_ms(), last_time) >= 1000:
            last_time = time.ticks_ms()
            temp = env_sensor.read_temperature()
            humi = env_sensor.read_humidity() 
            label_temp.setText("%.1fC"%temp)
            label_humi.setText("%.1f%%"%humi)
            cnt += 1
            if cnt == 5:
                cnt = 0
                publish_data(client)
        time.sleep_ms(100)

if __name__ == "__main__": 
    main()
