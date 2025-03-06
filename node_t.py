import configparser
import logging
import os
import queue
import random
import shutil
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

# 创建日志目录
log_directory = os.path.join(current_directory, "logs")
# 如果日志文件夹存在，则删除
if os.path.exists(log_directory):
    shutil.rmtree(log_directory)
os.makedirs(log_directory, exist_ok=True)  # 创建日志目录

def delayed_send(sender, receiver, message, delay_t=1.0):
    """
    模拟延迟发送消息
    1. 新开一个小线程
    :param message: 发送信息，信息包含。。。
    :param sender: 发送方
    :param receiver: 接收方
    # :param delay_t: 发送延迟
    """

    def _task():
        # jitter = random.uniform(-0.05, 0.05)  # 添加随机扰动（±0.05秒）
        # time.sleep(delay_t + jitter)
        # time.sleep(delay_t)
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
        self.enemies = []
        self.neighbor_table = {}
        self.buffered_neighbors = {}  # 缓冲区，存储邻居节点信息
        self.incoming_queue = queue.Queue()  # 消息队列
        self.last_cycle_msgs = []  # 缓存上一时刻的消息
        self.camp = camp  # 阵营：蓝色（"blue"） or 红色（"red"）

        # 加一把锁，用于 neighbor_table 的并发读写
        self._lock = threading.Lock()
        # 日志记录器
        self.logger = None


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
        # 日志文件路径（每个节点一个日志文件）
        log_file_path = os.path.join(log_directory, f"node_{self.node_id}_{self.camp}.log")
        self.logger = logging.getLogger(f"NodeLogger-{self.node_id}")
        self.logger.setLevel(logging.DEBUG)
        # 创建 FileHandler，并设置好输出格式
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s - Node-%(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        # 为避免重复添加 Handler，先判断是否已有 Handler
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

        # 不让日志传递到根 Logger，可设置
        self.logger.propagate = False

    def _apply_buffered_neighbors(self):
        """把上一轮缓冲的邻居数据应用到 neighbor_table"""
        with self._lock:
            if self.buffered_neighbors:
                for sender_id, message in self.buffered_neighbors.items():
                    # 记录日志
                    self.logger.debug(f"Node-{self.node_id} 应用上一轮邻居数据: {sender_id}: {message}")
                # self.logger.debug(f"Node-{self.node_id} 应用上一轮邻居数据: {[k for k in self.buffered_neighbors.keys()]}")
                self.neighbor_table = self.buffered_neighbors.copy()  # 更新 neighbor_table
                self.buffered_neighbors.clear()  # 清空缓冲区，为下一轮存储新的邻居信息

    def _update_neighbor_table(self, sender_id, message, arrival_time):
        """不立即更新邻居表，而是先存入缓冲区，下一轮再更新"""
        with self._lock:
            if sender_id not in self.buffered_neighbors:
                self.buffered_neighbors[sender_id] = {}

            self.buffered_neighbors[sender_id].update({
                "position": message["position"],
                "velocity": message["velocity"],
                "acceleration": message["acceleration"],
                "group_id": message["group_id"],
                # "neighbor_table": message["neighbor_table"],
                "last_send_time": message["send_time"],
                "last_recv_time": arrival_time
            })

    def _update_state(self):
        model = Model()
        model.calculate_movement(self, 1)

    def store_incoming(self, sender_id, message):
        """
        这里设置信息队列，存储接收到的信息
        """
        arrival_time = time.time()
        self.incoming_queue.put((sender_id, message, arrival_time))

    def _msg_send_to_neighbors(self):
        """
        向所有邻居发送消息, 每条消息都有一个固定延迟.
        也可以设计成对每个邻居不一样的延迟, 这里先简单处理.
        """
        message = {
            "id": self.node_id,
            "position": self.position,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "group_id": self.group_id,
            # "neighbor_table": self.neighbor_table,
            "send_time": time.time()
        }
        for neighbor in self.neighbors:
            # neighbor.store_incoming(self.node_id, message)
            delayed_send(sender=self, receiver=neighbor, message=message, delay_t=delay)
            log_msg = f"发送消息至 {neighbor.node_id}: {message}"
            self.logger.debug(log_msg)

    def _collect_incoming_for_next_cycle(self):
        """
        本时刻把 incoming_queue 里的新消息全部收集到 last_cycle_msgs，发送消息至
        这样下一时刻再处理它们
        """
        new_msgs = []
        while not self.incoming_queue.empty():
            sender_id, message, arrival_time = self.incoming_queue.get()
            new_msgs.append((sender_id, message, arrival_time))
        # # 把这批新消息放进 last_cycle_msgs
        # self.last_cycle_msgs.extend(new_msgs)
        # 把这批新消息存入 buffered_neighbors
        for sender_id, message, arrival_time in new_msgs:
            self._update_neighbor_table(sender_id, message, arrival_time)

    def stop(self):
        """
        停止节点。等待 run() 中的循环自然退出
        """
        self.running = False

    def run(self):
        """
        统一用一个循环模拟收发时间步：
          1) 处理上一时刻的消息 (last_cycle_msgs)
          2) 更新自身状态
          3) 发送本时刻的消息
          4) 收集当前时刻收到的消息 (incoming_queue)，留到下一时刻处理
        """
        while self.running:
            # 处理上一时刻的邻居数据
            self._apply_buffered_neighbors()
            # 更新自身运动状态 (如位置、速度)，相当于离散时间一步
            self._update_state()
            # 向所有邻居发送本时刻消息
            self._msg_send_to_neighbors()
            # 暂停1s，进入下一轮，发送频率为1hz
            time.sleep(1)
            # 收集下一时刻时刻收到的消息进行处理
            self._collect_incoming_for_next_cycle()


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

    def update_enemies_by_god(self, new_neighbors):
        pass


