import threading

from god import God

god = God()
if __name__ == "__main__":
    nodes = god.init_nodes("random","blue")

    print("所有节点的线程都结束了。")