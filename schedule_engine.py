"""
车辆调度AI算法评测系统 - 主调度引擎模块
包含: ConfigLoader, ScheduleSystem, ScheduleOutputGenerator
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import heapq
from collections import defaultdict


class TaskType(Enum):
    """任务类型枚举"""
    NORMAL = "normal"
    TEMPORARY = "temporary"
    EMERGENCY = "emergency"


class TaskStatus(Enum):
    """任务状态枚举"""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class TaskPhase(Enum):
    """任务阶段枚举"""
    IDLE = None
    GOING_TO_START = "going_to_start"
    LOADING = "loading"
    TRANSPORTING = "transporting"
    UNLOADING = "unloading"


@dataclass
class Node:
    """地图节点"""
    node_id: str
    node_type: str  # station/energy_station/material_station/switch
    x: float
    y: float
    connections: List[str] = field(default_factory=list)


@dataclass
class Edge:
    """地图边（路段）"""
    from_node: str
    to_node: str
    distance: float  # 米
    speed_limit: float  # m/min
    gradient: float  # 坡度 (-1到1)


@dataclass
class Task:
    """任务"""
    task_id: str
    start_node: str
    end_node: str
    load_weight: float  # 吨
    priority: int  # 1-99, 1最高
    task_type: TaskType
    status: TaskStatus
    material_tag: str = ""
    depends_on: List[str] = field(default_factory=list)
    time_window_start: Optional[float] = None
    time_window_end: Optional[float] = None
    created_time: Optional[float] = None


@dataclass
class Locomotive:
    """机车"""
    loco_id: str
    traction_type: str  # electric/diesel
    Q: float  # 载重能力（吨）
    max_speed: float  # 最大速度 m/min
    initial_node: str
    is_powered_on: bool
    is_schedulable: bool
    task_phase: Optional[str]
    current_task: Optional[str]
    # 电动
    battery: Optional[float] = None  # kWh
    # 柴油
    fuel_tank: Optional[float] = None  # L


class ConfigLoader:
    """配置文件加载器"""

    def __init__(self):
        self.map_config: Dict = {}
        self.tasks_config: Dict = {}
        self.locomotives_config: Dict = {}
        self.hyper_params: Dict = {}

    def load_map_config(self, filepath: str) -> Dict:
        """加载地图配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.map_config = json.load(f)
        self._validate_map_config()
        return self.map_config

    def load_tasks_config(self, filepath: str) -> Dict:
        """加载任务配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.tasks_config = json.load(f)
        self._validate_tasks_config()
        return self.tasks_config

    def load_locomotives_config(self, filepath: str) -> Dict:
        """加载机车配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.locomotives_config = json.load(f)
        self._validate_locomotives_config()
        return self.locomotives_config

    def load_hyper_params(self, filepath: str) -> Dict:
        """加载超参数配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.hyper_params = json.load(f)
        self._validate_hyper_params()
        return self.hyper_params

    def _validate_map_config(self):
        """验证地图配置"""
        # TODO: 实现地图配置验证逻辑
        pass

    def _validate_tasks_config(self):
        """验证任务配置"""
        # 验证priority范围
        for task in self.tasks_config.get('tasks', []):
            priority = task.get('priority', 50)
            if not (1 <= priority <= 99):
                raise ValueError(f"任务 {task['task_id']} 的priority必须在1-99之间")

            # 验证task_type
            task_type = task.get('task_type', 'normal')
            if task_type not in ['normal', 'temporary', 'emergency']:
                raise ValueError(f"任务 {task['task_id']} 的task_type必须为normal/temporary/emergency")

            # 验证status
            status = task.get('status', 'running')
            if status not in ['running', 'paused', 'completed']:
                raise ValueError(f"任务 {task['task_id']} 的status必须为running/paused/completed")

        # 验证依赖无循环
        self._check_circular_dependency()

    def _validate_locomotives_config(self):
        """验证机车配置"""
        for loco in self.locomotives_config.get('locomotives', []):
            # 电动机车验证battery
            if loco.get('traction_type') == 'electric':
                if 'battery' not in loco or loco['battery'] < 0:
                    raise ValueError(f"电动机车 {loco['loco_id']} 的battery字段必须存在且>=0")

            # 柴油机车验证fuel_tank
            if loco.get('traction_type') == 'diesel':
                if 'fuel_tank' not in loco or loco['fuel_tank'] < 0:
                    raise ValueError(f"柴油机车 {loco['loco_id']} 的fuel_tank字段必须存在且>=0")

    def _validate_hyper_params(self):
        """验证超参数配置"""
        precision = self.hyper_params.get('travel_time_precision', 2)
        if precision < 2:
            raise ValueError("travel_time_precision必须>=2")

    def _check_circular_dependency(self):
        """检查任务依赖是否存在循环"""
        tasks = self.tasks_config.get('tasks', [])
        task_ids = {t['task_id'] for t in tasks}

        # 构建依赖图
        graph = defaultdict(list)
        for task in tasks:
            task_id = task['task_id']
            for dep_id in task.get('depends_on', []):
                if dep_id not in task_ids:
                    raise ValueError(f"任务 {task_id} 依赖的任务 {dep_id} 不存在")
                graph[task_id].append(dep_id)

        # DFS检测循环
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for task_id in task_ids:
            if task_id not in visited:
                if has_cycle(task_id):
                    raise ValueError("任务依赖存在循环依赖")

    def load_all_configs(self, config_dir: str = 'configs') -> tuple:
        """加载所有配置文件"""
        self.load_map_config(f"{config_dir}/map_config.json")
        self.load_tasks_config(f"{config_dir}/tasks_config.json")
        self.load_locomotives_config(f"{config_dir}/locomotives_config.json")
        self.load_hyper_params(f"{config_dir}/hyper_params.json")
        return self.map_config, self.tasks_config, self.locomotives_config, self.hyper_params


class DijkstraPathCalculator:
    """Dijkstra最短路径计算器"""

    def __init__(self, map_config: Dict, hyper_params: Dict):
        self.nodes = {n['node_id']: n for n in map_config.get('nodes', [])}
        self.edges = map_config.get('edges', [])
        self.hyper_params = hyper_params
        self.adj_list = defaultdict(list)
        self._build_adjacency_list()

    def _build_adjacency_list(self):
        """构建邻接表"""
        for edge in self.edges:
            from_node = edge['from_node']
            to_node = edge['to_node']
            distance = edge['distance']
            speed_limit = edge.get('speed_limit', float('inf'))
            gradient = edge.get('gradient', 0)
            self.adj_list[from_node].append({
                'to_node': to_node,
                'distance': distance,
                'speed_limit': speed_limit,
                'gradient': gradient
            })

    def calculate_travel_time(self, distance: float, speed: float, gradient: float) -> float:
        """计算行驶时间，考虑坡度影响"""
        # 坡度修正系数
        gradient_factor = self.hyper_params.get('gradient_factor', 0.1)
        if gradient > 0:  # 上坡减速
            speed *= (1 - gradient * gradient_factor)
        elif gradient < 0:  # 下坡加速
            speed *= (1 + abs(gradient) * gradient_factor * 0.5)

        if speed <= 0:
            speed = 1  # 最小速度

        time = distance / speed  # 分钟
        return time

    def find_shortest_path(self, start: str, end: str, max_speed: float) -> tuple:
        """
        Dijkstra算法找最短路径
        返回: (路径列表, 总时间)
        """
        if start not in self.nodes or end not in self.nodes:
            return [], float('inf')

        # 优先队列: (时间, 当前节点, 路径)
        pq = [(0, start, [start])]
        visited = set()

        while pq:
            time, current, path = heapq.heappop(pq)

            if current in visited:
                continue
            visited.add(current)

            if current == end:
                return path, time

            for edge in self.adj_list[current]:
                neighbor = edge['to_node']
                if neighbor in visited:
                    continue

                # 计算实际速度（取路段限速和机车最大速度的较小值）
                actual_speed = min(edge['speed_limit'], max_speed)
                travel_time = self.calculate_travel_time(
                    edge['distance'],
                    actual_speed,
                    edge['gradient']
                )

                # 向上取整到时间精度
                precision = self.hyper_params.get('travel_time_precision', 2)
                travel_time = ((travel_time + precision - 0.01) // precision) * precision

                heapq.heappush(pq, (time + travel_time, neighbor, path + [neighbor]))

        return [], float('inf')

    def precompute_all_paths(self, locomotives: List[Locomotive]) -> Dict:
        """预计算所有机车从任意节点到任意节点的最短路径"""
        all_paths = {}
        for loco in locomotives:
            loco_id = loco.loco_id
            all_paths[loco_id] = {}
            for start_node in self.nodes:
                for end_node in self.nodes:
                    if start_node != end_node:
                        path, time = self.find_shortest_path(
                            start_node, end_node, loco.max_speed
                        )
                        all_paths[loco_id][(start_node, end_node)] = {
                            'path': path,
                            'time': time
                        }
        return all_paths


class ScheduleSystem:
    """调度系统主类"""

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.map_config = config_loader.map_config
        self.tasks_config = config_loader.tasks_config
        self.locomotives_config = config_loader.locomotives_config
        self.hyper_params = config_loader.hyper_params

        # 初始化路径计算器
        self.path_calculator = DijkstraPathCalculator(
            self.map_config, self.hyper_params
        )

        # 解析任务和机车
        self.tasks = self._parse_tasks()
        self.locomotives = self._parse_locomotives()

        # 预计算路径
        self.segment_speeds = {}

    def _parse_tasks(self) -> List[Task]:
        """解析任务配置"""
        tasks = []
        for t in self.tasks_config.get('tasks', []):
            task = Task(
                task_id=t['task_id'],
                start_node=t['start_node'],
                end_node=t['end_node'],
                load_weight=t.get('load_weight', 0),
                priority=t.get('priority', 50),
                task_type=TaskType(t.get('task_type', 'normal')),
                status=TaskStatus(t.get('status', 'running')),
                material_tag=t.get('material_tag', ''),
                depends_on=t.get('depends_on', []),
                time_window_start=t.get('time_window_start'),
                time_window_end=t.get('time_window_end'),
                created_time=t.get('created_time')
            )
            tasks.append(task)
        return tasks

    def _parse_locomotives(self) -> List[Locomotive]:
        """解析机车配置"""
        locomotives = []
        for l in self.locomotives_config.get('locomotives', []):
            loco = Locomotive(
                loco_id=l['loco_id'],
                traction_type=l['traction_type'],
                Q=l['Q'],
                max_speed=l['max_speed'],
                initial_node=l['initial_node'],
                is_powered_on=l.get('is_powered_on', True),
                is_schedulable=l.get('is_schedulable', True),
                task_phase=l.get('task_phase'),
                current_task=l.get('current_task'),
                battery=l.get('battery'),
                fuel_tank=l.get('fuel_tank')
            )
            locomotives.append(loco)
        return locomotives

    def get_available_locomotives(self) -> List[Locomotive]:
        """获取可用机车（开机且可调度）"""
        return [
            loco for loco in self.locomotives
            if loco.is_powered_on and loco.is_schedulable
        ]

    def solve(self, strategy: str = 'baseline') -> Dict:
        """
        执行调度求解
        strategy: 策略名称
        返回: 调度结果字典
        """
        # TODO: 实现具体的调度逻辑
        # 基准策略使用CP-SAT
        # 候选策略调用对应的策略模块
        raise NotImplementedError("子类实现")


class ScheduleOutputGenerator:
    """调度输出生成器"""

    def __init__(self, schedule_result: Dict):
        self.result = schedule_result

    def generate_output(self) -> Dict:
        """生成schedule_output.json格式的输出"""
        output = {
            'solve_status': self.result.get('solve_status', 'unknown'),
            'makespan': self.result.get('makespan', 0),
            'strategy': self.result.get('strategy', 'unknown'),
            'timestamp': self.result.get('timestamp'),
            'assignments': []
        }

        for assignment in self.result.get('assignments', []):
            output['assignments'].append({
                'loco_id': assignment['loco_id'],
                'task_sequence': assignment['task_sequence'],
                'timeline': assignment.get('timeline', [])
            })

        return output

    def save_output(self, filepath: str):
        """保存输出到JSON文件"""
        output = self.generate_output()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # 测试代码
    print("车辆调度AI算法评测系统 - 调度引擎模块")