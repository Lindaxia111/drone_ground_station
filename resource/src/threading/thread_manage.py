import functools
import threading
import time

class ThreadNode:
    def __init__(self, name):
        self.name = name
        self.stop_event = threading.Event()
        self.thread = None

    def run(self, func_arg, *args):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()  # 确保新的线程运行时清除停止信号
            wrapped_func = functools.partial(func_arg, self.stop_event)  # 预先绑定 stop_event
            self.thread = threading.Thread(target=func_arg, args=(self.stop_event, *args), daemon=True)
            self.thread.start()
            print(f"Thread {self.name} started.")
        else:
            print(f"Thread {self.name} is already running.")

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()
            print(f"Thread {self.name} stopped.")
        else:
            print(f"Thread {self.name} is not running.")

class ThreadManager:
    def __init__(self):
        self.threads = {}  # 存储线程名称和线程对象
    
    def add_thread(self, name):
        if name not in self.threads:
            self.threads[name] = ThreadNode(name)
            print(f"Thread {name} added.")
        else:
            print(f"Thread {name} already exists.")
    
    def run_thread(self, name, func_arg, *args):
        if name in self.threads:
            self.threads[name].run(func_arg, *args)
        else:
            print(f"Thread {name} not found.")
    
    def stop_thread(self, name):
        if name in self.threads:
            self.threads[name].stop()
            del self.threads[name]  # 停止后移除线程对象
            print(f"Thread {name} removed from manager.")
        else:
            print(f"Thread {name} not found.")
    
    def list_threads(self):
        return list(self.threads.keys())

# 示例任务
def sample_task(stop_event):
    while not stop_event.is_set():
        print("Hello from Worker1")
        time.sleep(1)

# 示例任务
def sample_task1(stop_event):
    while not stop_event.is_set():
        print("Nihao from Worker1")
        time.sleep(1)

if __name__ == "__main__":
    manager = ThreadManager()
    manager.add_thread("Worker1")
    manager.add_thread("Worker2")
    manager.run_thread("Worker1", sample_task)
    manager.run_thread("Worker2", sample_task1)
    time.sleep(5)
    
    manager.stop_thread("Worker1")
