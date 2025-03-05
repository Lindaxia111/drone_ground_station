import configparser
import os
import queue
import threading
import time

from model import Model

# 获取当前脚本所在路径
current_directory = os.path.dirname(os.path.abspath(__file__))
# 构造配置文件的路径
config_file_path = os.path.join(current_directory, 'config/config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
# 读取配置文件中的发送延迟
delay = float(config.get("send_delay", "DELAY"))

def delayed_send(sender, receiver, message, delay_t=1.0):
    """
    模拟延迟发送消息
    1. 新开一个小线程
    2. 等待 delay 秒后,调用 receiver.store_incoming(...) 存储消息
    :param message: 发送信息，信息包含。。。
    :param sender: 发送方
    :param receiver: 接收方
    :param delay_t: 发送延迟
    """

    def _task():
        # 等待指定延迟
        time.sleep(delay_t)
        receiver.store_incoming(sender.node_id, message)
    threading.Thread(target=_task, daemon=True).start()

class Node:
    def __init__(self, god, camp):
        self.running = True
        self.god = god
        self.node_id = None
        self.position = None
        self.velocity = None
        self.direction = None
        self.acceleration = None
        self.group_id = 0
        self.neighbors = []
        self.neighbor_table = {}
        self.incoming_queue = queue.Queue()  # 消息队列
        self.camp = camp  # 阵营：蓝色（"blue"） or 红色（"red"）

        # 加一把锁，用于 neighbor_table 的并发读写
        self._lock = threading.Lock()

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

    def update_state(self):
        model = Model()
        while self.running:
            model.calculate_movement(self, 1)
            # print(f"Node-{self.node_id} position: {self.position}, velocity: {self.velocity}, acceleration: {self.acceleration}")
            time.sleep(1)

    def update_neighbors_by_god(self, new_neighbors):
        """
        通过god实时更新邻居节点，要从 neighbor_table 里删除那些已经不在 new_neighbors 列表中的“旧邻居”。
        :param new_neighbors: 实时邻居节点
        """
        with self._lock:
            self.neighbors = new_neighbors
            # 2) 得到新邻居的 ID 集合
            new_ids = set()
            for nb in new_neighbors:
                # 如果 nb 是 Node 对象，就用 nb.node_id
                if hasattr(nb, 'node_id'):
                    new_ids.add(nb.node_id)
            # 当前 neighbor_table 中记录的旧邻居
            old_ids = set(self.neighbor_table.keys())
            # 做差集，找出那些已经不在新邻居列表里的节点
            to_remove = old_ids - new_ids
            # 把差集从 neighbor_table 中删除
            for rid in to_remove:
                del self.neighbor_table[rid]

    def store_incoming(self, sender_id, message):
        """
        这里设置信息队列，存储接收到的信息
        """
        arrival_time = time.time()
        self.incoming_queue.put((sender_id, message, arrival_time))

    def msg_send(self):
        """
        向所有邻居发送消息, 每条消息都有一个固定延迟.
        也可以设计成对每个邻居不一样的延迟, 这里先简单处理.
        """
        while self.running:
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
                delayed_send(sender=self, receiver=neighbor, message=message, delay_t=delay)
                # print(f"Node-{self.node_id} send message to Node-{neighbor.node_id}\n")
            # 间隔1秒，再发送下一次
            time.sleep(1)

    def msg_receive(self):
        """
        从消息队列中读取消息
        """
        while self.running:
            try:
                sender_id, message, arrival_time = self.incoming_queue.get(timeout=1)
                # 从消息中提取邻居表
                self._update_neighbor_table(sender_id, message, arrival_time)
            except queue.Empty:
                continue

    def _update_neighbor_table(self, sender_id, message, arrival_time):
        # 这里给写 neighbor_table 加锁
        with self._lock:
            if sender_id not in self.neighbor_table:
                self.neighbor_table[sender_id] = {}
            self.neighbor_table[sender_id].update({
                "position": message["position"],
                "velocity": message["velocity"],
                "acceleration": message["acceleration"],
                "group_id": message["group_id"],
                "last_send_time": message["timestamp"],
                "last_recv_time": arrival_time
            })

    def stop(self):
        """
        停止节点。等待 run() 中的循环自然退出
        """
        self.running = False

    def run(self):
        """
        节点运行, 开启一个线程用于消息传输
        """
        t = threading.Thread(target=self.msg_send, name=f"NodeThread-{self.node_id}")
        t.daemon = True
        t.start()

        t = threading.Thread(target=self.msg_receive, name=f"NodeThread-{self.node_id}")
        t.daemon = True
        t.start()

        t = threading.Thread(target=self.update_state, name=f"NodeThread-{self.node_id}")
        t.daemon = True
        t.start()


