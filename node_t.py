import configparser
import os
import threading
import time

# 获取当前脚本所在路径
current_directory = os.path.dirname(os.path.abspath(__file__))
# 构造配置文件的路径
config_file_path = os.path.join(current_directory, 'config/config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
# 读取配置文件中的发送延迟
delay = float(config.get("send_delay", "DELAY"))

def delayed_send(sender, receiver, message, delay=1.0):
    """
    模拟延迟发送消息
    :param message: 发送信息，信息包含。。。
    :param sender: 发送方
    :param receiver: 接收方
    :param delay: 发送延迟
    """

    def _task():
        # 等待指定延迟
        time.sleep(delay)
        receiver.store_incoming(sender.node_id, message)
    # 新开一个小线程等待 delay 秒后,调用 receiver.store_incoming(...) 存储消息
    threading.Thread(target=_task, daemon=True).start()

class Node:
    def __init__(self, god, camp):
        self.god = god
        self.node_id = None
        self.position = None
        self.velocity = None
        self.direction = None
        self.acceleration = None
        self.group_id = 0
        self.neighbors = []
        self.neighbor_table = {}
        self.camp = camp  # 阵营：蓝色（"blue"） or 红色（"red"）

    def init_state(self, node_id, pos, vel, acc):
        """
        初始化节点状态
        :param node_id: 节点ID
        :param pos: 节点位置[x, y]
        :param vel: 节点速度[vx, vy]
        :param acc: 节点加速度[ax, ay]
        """
        self.node_id = node_id
        self.position = pos
        self.velocity = vel
        self.acceleration = acc


    def update_neighbors_by_god(self, neighbors):
        """
        通过god实时更新邻居节点
        :param neighbors:实时邻居节点
        """
        self.neighbors = neighbors

    def store_incoming(self, sender_id, message):
        """
        存储收到的消息
        :param sender_id: 发送方ID
        :param message: 消息内容
        """
        if sender_id not in self.neighbor_table:
            self.neighbor_table[sender_id] = message
        else:
            self.neighbor_table[sender_id].update(message)

    def msg_transfer(self):
        """
        向所有邻居发送消息, 每条消息都有一个固定延迟.
        也可以设计成对每个邻居不一样的延迟, 这里先简单处理.
        """
        while True:
            message = {
                "id": self.node_id,
                "position": self.position,
                "velocity": self.velocity,
                "acceleration": self.acceleration,
                "group_id": self.group_id,
                "neighbor_table": self.neighbor_table,
                "timestamp": time.time()
            }
            for neighbor in self.neighbors:
                delayed_send(sender=self, receiver=neighbor, message=message, delay=delay)

    def run(self):
        """
        节点运行, 开启一个线程用于消息传输
        """
        t = threading.Thread(target=self.msg_transfer, name=f"NodeThread-{self.node_id}")
        t.daemon = True
        t.start()


