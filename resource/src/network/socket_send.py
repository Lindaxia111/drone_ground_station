import logging
import socket
import time
import threading
import json
import random
import math
import configparser
import os


# 获取当前脚本所在路径
current_directory = os.path.dirname(os.path.abspath(__file__))
# 构造配置文件的路径
config_file_path = os.path.join(current_directory, '../../config/net_config.ini')

# 1. 节点类：用于创建通讯节点
class Node:
    def __init__(self, node_id, flag):
        # 节点id
        self.node_id = node_id
        # 节点其余信息
        self.position = [random.randint(0, 100), random.randint(0, 100)] # 创建的随机位置
        self.velocity = random.randint(1, 10) # 创建的随机速度
        self.direction = random.randint(0, 360) # 创建的随机方向
        self.neighbor_table = {} # 邻居表

        # 获取组播ip地址和端口号
        self.ip = None
        self.port = None
        # 创建ConfigParser对象
        self.config = configparser.ConfigParser()
        # 读取配置文件
        self.config.read(config_file_path)
        # 获取对应的IP地址和端口号
        if flag is not None and "red" in flag:
            self.ip = self.config.get("network", "RED_IP")
            self.port = int(self.config.getint("network", "RED_PORT")) + node_id
        elif flag is not None and "blue" in flag:
            self.ip = self.config.get("network", "BLUE_IP")
            self.port = int(self.config.getint("network", "BLUE_PORT")) + node_id
        else:
            logging.error("节点未分配阵营，节点无效!")

        if self.ip is not None and self.port is not None:
            logging.info("节点创建成功！")
            self.group = (self.ip, self.port)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('', self.port))
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            mreq = socket.inet_aton(self.ip) + socket.inet_aton("0.0.0.0")
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def calculate_distance(self, other_node):
        x1, y1 = self.position
        x2, y2 = other_node.position
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def send_msg(self):
        info = {
            "node_id": self.node_id,
            "position": self.position,
            "velocity": self.velocity,
            "direction": self.direction,
            "neighbor_table": self.neighbor_table
        }
        message = json.dumps(info).encode("utf-8") # 将字典转换为json字符串
        self.socket.sendto(message, self.group)
        logging.info(f"节点{self.node_id}发送消息成功！")

    def receive_msg(self):
        while True:
            data, addr = self.socket.recvfrom(1024)
            info = json.loads(data.decode("utf-8"))
            logging.info(f"节点{self.node_id}接收到消息！")
            logging.info(f"消息内容：{info}")
            try:
                self.update_neighbor_table(data)
            except Exception as e:
                logging.error(f"更新邻居表失败！{e}")

    def start_sending(self):
        while True:
            self.send_msg()
            time.sleep(1)  # 每秒发送一次信息

    def update_neighbor_table(self, other_node_info):
        other_node = json.loads(other_node_info)
        other_node_id = other_node['node_id']
        other_position = other_node['position']
        other_velocity = other_node['velocity']
        other_direction = other_node['direction']

        distance = self.calculate_distance(Node(other_node_id))
        if distance < 10:  # 距离小于10认为是邻居
            self.neighbor_table[other_node_id] = {
                "position": other_position,
                "velocity": other_velocity,
                "direction": other_direction
            }
            print(f"Node {self.node_id} updated its neighbor table with node {other_node_id}")

    def run(self):
        receive_thread = threading.Thread(target=self.receive_msg)
        receive_thread.daemon = True
        receive_thread.start()

        send_thread = threading.Thread(target=self.send_msg())
        send_thread.daemon = True
        send_thread.start()

# 模拟多个节点，形成网状拓扑
if __name__ == "__main__":
    nodes = []
    for node_id in range(1, 5):
        node = Node(node_id, "red")
        nodes.append(node)
        threading.Thread(target=node.run).start()

    while True:
        time.sleep(1)
# node = Node(1, "red")
# print(node.ip, node.port)