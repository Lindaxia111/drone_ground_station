from flask import Flask, jsonify, render_template
from god import God
import threading
import time

app = Flask(__name__)

# 创建 God 实例
god = God()
# 初始化一些节点（比如 5 个蓝色节点、5 个红色节点）
god.init_nodes("random", "blue", 50,(0,10),(0,10),(0,1),(0,1),(0,0.1),(0,0.1))
god.init_nodes("random", "red", 5,(300,290),(300,300),(-1,0),(-1,0),(-0.1,0),(-0.1,0))
# 启动节点线程和邻居更新线程
god.run()

@app.route('/')
def index():
    return render_template('index.html')  # 渲染templates目录下的index.html

@app.route('/nodes', methods=['GET'])
def get_nodes():
    """
    返回所有节点的动态信息，包括坐标和邻居列表
    """
    data = []
    # 将所有节点合并
    all_nodes = god.blue_nodes + god.red_nodes

    for node in all_nodes:
        with node._lock:
            neighbor_ids = list(node.neighbor_table.keys())
            # 根据阵营设置不同的颜色
            color = 'blue' if node.camp == 'blue' else 'red'

            data.append({
                "node_id": node.node_id,
                "camp": node.camp,
                "color": color,
                "position": node.position,
                "velocity": node.velocity,
                "acceleration": node.acceleration,
                "neighbor_ids": neighbor_ids
            })

    return jsonify(data)


if __name__ == '__main__':
    # 直接启动 Flask, 监听 5000 端口
    app.run(host='0.0.0.0', port=5000, debug=False)
