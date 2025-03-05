import threading

from god import God

god = God()
if __name__ == "__main__":
    god.init_nodes("random","blue", 5)
    god.run()
