


class Model:
    def __init__(self):
        self.type = 0

    @staticmethod
    def calculate_movement(node, time_step):
        """
        计算节点的运动状态
        :param time_step: 计算时间步长
        :param node: 节点
        """
        node.position[0] = node.position[0] + node.velocity[0] * time_step
        node.position[1] = node.position[1] + node.velocity[1] * time_step

        node.velocity[0] = node.velocity[0] + node.acceleration[0] * time_step
        node.velocity[1] = node.velocity[1] + node.acceleration[1] * time_step