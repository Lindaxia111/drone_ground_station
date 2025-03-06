from datetime import datetime

def timestamp_to_datetime(timestamp):
    """将时间戳转换为可读的时间字符串"""
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime("%Y-%m-%d %H:%M:%S")

# 示例
timestamp =1741249199.629442
print(timestamp_to_datetime(timestamp))  # 输出格式: YYYY-MM-DD HH:MM:SS
