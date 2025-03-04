import configparser
import math
import os
import random

from node_t import Node

# 获取当前脚本所在路径
current_directory = os.path.dirname(os.path.abspath(__file__))
# 构造配置文件的路径
config_file_path = os.path.join(current_directory, 'config/config.ini')

class God:
    def __init__(self):
        self.blue_nodes = []
        self.red_nodes = []
        self.neighbor_distance = 2.0
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.neighbor_distance = float(config.get("network", "NEIGHBOR_DISTANCE"))
        self.enemy_distance = float(config.get("network", "ENEMY_DISTANCE"))

    @staticmethod
    def calculate_distance(position1, position2):
        """
        计算两节点之间的欧几里得距离
        :param position1: 节点1的位置
        :param position2: 节点2的位置
        :return: 两节点之间的距离
        """
        return math.sqrt((position2[0] - position1[0]) ** 2 + (position2[1] - position1[1]) ** 2)

    def init_nodes(self, method, camp=None, n=0,
                   x_range=(0, 1), y_range=(0, 1),
                   vx_range=(0, 1), vy_range=(0, 1),
                   ax_range=(0, 0), ay_range=(0, 1)):
        """
        根据不同的方法初始化节点，包括随机初始化和从文件中读取初始化
        参数说明
        :param method: “random”表示按照给定的位置、速度和加速度边界值随机生成，“file”表示从文件创造节点
        :param camp: 节点的阵营，包括“blue”和“red”
        :param n: 随机生成时需要创建的节点个数
        :param x_range: 节点的x坐标范围
        :param y_range: 节点的y坐标范围
        :param vx_range: 节点的x方向速度范围
        :param vy_range: 节点的y方向速度范围
        :param ax_range: 节点的x方向加速度范围
        :param ay_range: 节点的y方向加速度范围
        :return:
        """

        nodes = []

        if method == "random":
            if camp is None:
                raise ValueError("随机创建节点时，需要指定阵营！")
            for i in range(n):
                node_id = i
                x = random.uniform(*x_range)
                y = random.uniform(*y_range)
                vx = random.uniform(*vx_range)
                vy = random.uniform(*vy_range)
                ax = random.uniform(*ax_range)
                ay = random.uniform(*ay_range)

                node = Node(self, camp)
                node.init_state(node_id, [x, y], [vx, vy], [ax, ay])
                nodes.append(node)
        elif method == "file":
            """
            文件名命名为：nodes.txt, 放在config文件夹下 
            从文件中读取节点信息文件，文件格式如下：
            node_id color x y vx vy ax ay
            实例： 1 blue 1.0 1.0 1.0 1.0 0.1 0.1
            表示为节点1，阵营为蓝色，位置为(1.0, 1.0)，速度为(1.0, 1.0)，加速度为(0.1, 0.1)
            """
            try:
                with open('config/config.ini', 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if not parts:
                            continue
                        node_id = int(parts[0])
                        color_from_file = parts[1]
                        x = float(parts[2])
                        y = float(parts[3])
                        vx = float(parts[4])
                        vy = float(parts[5])
                        ax = float(parts[6])
                        ay = float(parts[7])

                        node = Node(self, color_from_file)
                        node.init_state(node_id, [x, y], [vx, vy], [ax, ay])
                        nodes.append(node)
            except FileNotFoundError:
                print("读取文件不存在！")

        if camp == "blue":
            self.blue_nodes = nodes
        elif camp == "red":
            self.red_nodes = nodes
        else:
            raise ValueError("阵营错误！")

    def update_blue_neighbors(self):
        """
        更新当前蓝色节点的邻居节点
        """
        if len(self.blue_nodes) <= 1:
            return
        for node in self.blue_nodes:
            neighbors = []
            for other in self.blue_nodes:
                if node.node_id == other.node_id:
                    continue
                distance = self.calculate_distance(node.pos, other.pos)
                if distance < self.neighbor_distance:
                    neighbors.append(other)
            node.update_neighbors_by_god(neighbors)

    def update_red_neighbors(self):
        """
        更新当前红色节点的邻居节点
        """
        if len(self.red_nodes) <= 1:
            return
        for node in self.red_nodes:
            neighbors = []
            for other in self.red_nodes:
                if node.node_id == other.node_id:
                    continue
                distance = self.calculate_distance(node.pos, other.pos)
                if distance < self.neighbor_distance:
                    neighbors.append(other)
            node.update_neighbors_by_god(neighbors)

    @staticmethod
    def run_node_in_thread(node):
        """
        这是一个包装函数，用来在线程内执行 node.run()。
        """
        node.run()

