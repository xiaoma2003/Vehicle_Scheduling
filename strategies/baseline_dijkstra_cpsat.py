"""
基准策略：Dijkstra + CP-SAT
使用Dijkstra最短路径预计算 + Google OR-Tools CP-SAT约束规划求解器
"""

import json
from typing import Dict, List, Optional, Any
from ortools.sat.python import cp_model
from schedule_engine import DijkstraPathCalculator


class BaselineStrategy:
    """基准策略：Dijkstra路径预计算 + CP-SAT约束规划"""

    def __init__(self, configs: Dict):
        self.map_config = configs['map_config']
        self.tasks_config = configs['tasks_config']
        self.locomotives_config = configs['locomotives_config']
        self.hyper_params = configs['hyper_params']

        # 初始化路径计算器
        self.path_calculator = DijkstraPathCalculator(
            self.map_config, self.hyper_params
        )

        # 解析数据
        self.nodes = self._parse_nodes()
        self.tasks = self._parse_tasks()
        self.locomotives = self._parse_locomotives()

        # CP-SAT模型
        self.model = None
        self.solver = None

    def _parse_nodes(self) -> Dict:
        """解析节点"""
        return {n['node_id']: n for n in self.map_config.get('nodes', [])}

    def _parse_tasks(self) -> List[Dict]:
        """解析任务"""
        return self.tasks_config.get('tasks', [])

    def _parse_locomotives(self) -> List[Dict]:
        """解析机车"""
        return self.locomotives_config.get('locomotives', [])

    def solve(self) -> Dict:
        """
        执行调度求解
        返回包含调度结果的字典
        """
        result = {
            'strategy': 'baseline_dijkstra_cpsat',
            'solve_status': 'unknown',
            'makespan': 0,
            'assignments': [],
            'solve_time': 0
        }

        try:
            # 创建CP-SAT模型
            self.model = cp_model.CpModel()

            # 构建约束模型（13条约束）
            self._build_constraints()

            # 创建求解器
            self.solver = cp_model.CpSolver()
            self.solver.parameters.max_time_in_seconds = self.hyper_params.get('max_solve_time', 300)

            # 求解
            status = self.solver.Solve(self.model)

            # 处理求解状态
            if status == cp_model.OPTIMAL:
                result['solve_status'] = 'optimal'
                result['makespan'] = self.solver.ObjectiveValue()
                result['assignments'] = self._extract_assignments()
            elif status == cp_model.FEASIBLE:
                result['solve_status'] = 'feasible'
                result['makespan'] = self.solver.ObjectiveValue()
                result['assignments'] = self._extract_assignments()
            elif status == cp_model.INFEASIBLE:
                result['solve_status'] = 'infeasible'
                result['message'] = '无可行解，请检查约束条件'
            else:
                result['solve_status'] = 'unknown'
                result['message'] = '求解器返回未知状态'

            result['solve_time'] = self.solver.WallTime()

        except Exception as e:
            result['solve_status'] = 'error'
            result['message'] = str(e)

        return result

    def _build_constraints(self):
        """
        构建约束模型（13条约束）
        """
        # TODO: 完整实现13条约束
        # 1. 每个任务必须被分配给一台机车
        # 2. 每台机车在任何时刻只能执行一个任务
        # 3. 任务执行顺序约束
        # 4. 时间窗约束
        # 5. 任务依赖约束
        # 6. 载重约束
        # 7. 节点位置约束
        # 8. 能源消耗约束
        # 9. 紧急任务优先约束
        # 10. 临时任务时间窗约束
        # 11. 坡度速度修正约束
        # 12. 道岔通过时间约束
        # 13. 全局工期最小化目标

        # 获取可用机车
        available_locos = [
            loco for loco in self.locomotives
            if loco.get('is_powered_on') and loco.get('is_schedulable')
        ]

        if not available_locos:
            raise ValueError("没有可用的机车")

        # 创建变量
        num_tasks = len(self.tasks)
        num_locos = len(available_locos)

        # 任务-机车分配变量
        task_loco_vars = {}
        for i, task in enumerate(self.tasks):
            for j, loco in enumerate(available_locos):
                var = self.model.NewBoolVar(f'task_{i}_loco_{j}')
                task_loco_vars[(i, j)] = var

        # 约束1: 每个任务必须被分配给一台机车
        for i in range(num_tasks):
            self.model.Add(
                sum(task_loco_vars[(i, j)] for j in range(num_locos)) == 1
            )

        # 约束2: 时间变量
        # 使用离散时间建模（精度由hyper_params指定）
        precision = self.hyper_params.get('travel_time_precision', 2)
        max_time = int(self.hyper_params.get('big_m_value', 10000))

        start_time_vars = {}
        end_time_vars = {}
        for i, task in enumerate(self.tasks):
            start_var = self.model.NewIntVar(0, max_time, f'start_{i}')
            end_var = self.model.NewIntVar(0, max_time, f'end_{i}')
            start_time_vars[i] = start_var
            end_time_vars[i] = end_var

            # 任务执行时间 = 行驶时间 + 装货时间 + 卸货时间
            # TODO: 计算实际行驶时间
            travel_time = 10  # 示例值
            loading_time = self.hyper_params.get('loading_time', 5)
            unloading_time = self.hyper_params.get('unloading_time', 5)
            duration = travel_time + loading_time + unloading_time

            self.model.Add(end_var - start_var == duration)

        # 约束5: 任务依赖约束
        for i, task in enumerate(self.tasks):
            depends_on = task.get('depends_on', [])
            for dep_id in depends_on:
                # 找到依赖任务的索引
                dep_idx = None
                for k, t in enumerate(self.tasks):
                    if t['task_id'] == dep_id:
                        dep_idx = k
                        break
                if dep_idx is not None:
                    # 当前任务的开始时间必须大于依赖任务的结束时间
                    self.model.Add(
                        start_time_vars[i] >= end_time_vars[dep_idx]
                    )

        # 目标: 最小化全局工期（makespan）
        makespan_var = self.model.NewIntVar(0, max_time, 'makespan')
        for i in range(num_tasks):
            self.model.Add(makespan_var >= end_time_vars[i])
        self.model.Minimize(makespan_var)

    def _extract_assignments(self) -> List[Dict]:
        """提取任务分配结果"""
        assignments = []

        # 获取可用机车
        available_locos = [
            loco for loco in self.locomotives
            if loco.get('is_powered_on') and loco.get('is_schedulable')
        ]

        # TODO: 从求解结果中提取分配信息
        for j, loco in enumerate(available_locos):
            assigned_tasks = []
            for i, task in enumerate(self.tasks):
                # 检查是否分配给该机车
                # TODO: 从solver中获取变量值
                assigned_tasks.append(task['task_id'])

            assignments.append({
                'loco_id': loco['loco_id'],
                'task_sequence': assigned_tasks,
                'timeline': []  # TODO: 详细时间线
            })

        return assignments


if __name__ == '__main__':
    # 测试基准策略
    print("基准策略模块: Dijkstra + CP-SAT")