# drone_ground_station
## 目标
1. 环境信息的设置推演
2. 红蓝双方信息的和更新监控
3. 态势信息试试更新同步红蓝双方

## 无人机组成结构
> 无人机个体作为作战中的最小系统，该系统由任务系统、态势感知和个体规划组成
1. 无人机态势感知 
> 负责通过本体传感器、邻居无人机和外部感知搜索获取信息数据，并将信息传入
 >* 个体态势： 自身位置、速度、加速度、转向角
 >* 群组态势： 群组内邻居信息
 >* 环境态势： 天气信息，地形信息
 >* 对方态势： 红方态势，蓝方态势，目标状态
 >>环境态势和对方态势通过中央服务器进行计算得出来模拟无人机感知
2. 无人机信息传输


改初始化：
1、随机生成
2、根据文档生成 （id， vel，pos，加速度 ）

 

god进行邻居计算和enemy计算,碰撞检测                             

传输时仅传输msg，msg打上时间戳，邻居信息时间比自己慢一个时间戳
msg: [id,pos,vel,acc,timestamp,neighbors,mission_res]

neighbors =[ 
[id,pos,vel,acc,timestamp,neighbors]
[id,pos,vel,acc,timestamp,neighbors]
[id,pos,vel,acc,timestamp,neighbors]
[id,pos,vel,acc,timestamp,neighbors]
]

