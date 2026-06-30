"""
车辆调度AI算法评测系统 - API接口模块
包含ScheduleAPI类的16个接口方法
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from schedule_engine import ConfigLoader, ScheduleSystem, ScheduleOutputGenerator
from schedule_database import ScheduleDatabase


class ScheduleAPI:
    """调度系统API接口类 - 封装16个方法供前端调用"""

    def __init__(self, config_dir: str = 'configs', db_path: str = 'database/schedule_history.db'):
        self.config_dir = config_dir
        self.config_loader = ConfigLoader()
        self.db = ScheduleDatabase(db_path)
        self.current_batch_id = None

    # ==================== 配置管理接口 ====================

    def load_configurations(self, config_dir: str = None) -> Dict:
        """
        接口1: 加载所有配置文件
        返回: 包含地图、任务、机车、超参数配置的字典
        """
        config_dir = config_dir or self.config_dir
        try:
            map_config, tasks_config, locos_config, hyper_params = \
                self.config_loader.load_all_configs(config_dir)
            return {
                'status': 'success',
                'data': {
                    'map_config': map_config,
                    'tasks_config': tasks_config,
                    'locomotives_config': locos_config,
                    'hyper_params': hyper_params
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def save_configuration(self, config_type: str, config_data: Dict) -> Dict:
        """
        接口2: 保存配置文件
        config_type: map/tasks/locomotives/hyper_params
        返回: 操作结果
        """
        valid_types = ['map', 'tasks', 'locomotives', 'hyper_params']
        if config_type not in valid_types:
            return {'status': 'error', 'message': f'无效的配置类型: {config_type}'}

        filename_map = {
            'map': 'map_config.json',
            'tasks': 'tasks_config.json',
            'locomotives': 'locomotives_config.json',
            'hyper_params': 'hyper_params.json'
        }

        filepath = f"{self.config_dir}/{filename_map[config_type]}"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return {'status': 'success', 'message': f'{config_type}配置已保存'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def validate_configuration(self, config_type: str, config_data: Dict) -> Dict:
        """
        接口3: 验证配置数据
        返回: 验证结果
        """
        try:
            if config_type == 'map':
                # 验证地图配置
                if 'nodes' not in config_data or 'edges' not in config_data:
                    return {'status': 'error', 'message': '地图配置缺少nodes或edges字段'}
                # TODO: 更多验证逻辑

            elif config_type == 'tasks':
                # 验证任务配置
                tasks = config_data.get('tasks', [])
                for task in tasks:
                    priority = task.get('priority', 50)
                    if not (1 <= priority <= 99):
                        return {'status': 'error',
                                'message': f"任务 {task.get('task_id')} 的priority必须在1-99之间"}

            elif config_type == 'locomotives':
                # 验证机车配置
                locos = config_data.get('locomotives', [])
                for loco in locos:
                    if loco.get('traction_type') == 'electric':
                        if loco.get('battery', -1) < 0:
                            return {'status': 'error',
                                    'message': f"电动机车 {loco.get('loco_id')} 的battery必须>=0"}
                    elif loco.get('traction_type') == 'diesel':
                        if loco.get('fuel_tank', -1) < 0:
                            return {'status': 'error',
                                    'message': f"柴油机车 {loco.get('loco_id')} 的fuel_tank必须>=0"}

            elif config_type == 'hyper_params':
                # 验证超参数配置
                precision = config_data.get('travel_time_precision', 2)
                if precision < 2:
                    return {'status': 'error', 'message': 'travel_time_precision必须>=2'}

            return {'status': 'success', 'message': '验证通过'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # ==================== 调度执行接口 ====================

    def execute_scheduling(self, strategies: List[str] = None,
                           compare_mode: bool = False) -> Dict:
        """
        接口4: 执行调度
        strategies: 要执行的策略列表，None表示仅基准策略
        compare_mode: 是否启用多策略对比模式
        返回: 调度结果
        """
        try:
            # 生成batch_id
            self.current_batch_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + str(uuid.uuid4())[:8]

            # 加载配置
            configs = self.load_configurations()
            if configs['status'] == 'error':
                return configs

            # 保存配置到数据库
            self.db.save_map_config(self.current_batch_id, configs['data']['map_config'])
            self.db.save_tasks_config(self.current_batch_id, configs['data']['tasks_config'])
            self.db.save_locomotives_config(self.current_batch_id, configs['data']['locomotives_config'])
            self.db.save_hyper_params(self.current_batch_id, configs['data']['hyper_params'])

            # 记录日志
            self.db.log(self.current_batch_id, 'INFO', 'SCHEDULING',
                        f'开始调度执行，策略: {strategies}, 对比模式: {compare_mode}')

            results = []

            if compare_mode and strategies:
                # 多策略对比模式
                for strategy in strategies:
                    result = self._execute_single_strategy(strategy, configs['data'])
                    results.append(result)

                # 生成对比报告
                comparison = self._generate_comparison_report(results)
                self.db.save_comparison_report(
                    self.current_batch_id,
                    strategies,
                    comparison.get('best_strategy'),
                    comparison
                )
            else:
                # 单策略模式
                strategy = strategies[0] if strategies else 'baseline'
                result = self._execute_single_strategy(strategy, configs['data'])
                results.append(result)

            return {
                'status': 'success',
                'batch_id': self.current_batch_id,
                'results': results,
                'compare_mode': compare_mode
            }

        except Exception as e:
            self.db.log(self.current_batch_id, 'ERROR', 'SCHEDULING',
                       f'调度执行失败: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _execute_single_strategy(self, strategy: str, configs: Dict) -> Dict:
        """执行单个策略"""
        # TODO: 根据策略名称调用对应的策略模块
        if strategy == 'baseline':
            # 调用基准策略
            from strategies.baseline_dijkstra_cpsat import BaselineStrategy
            solver = BaselineStrategy(configs)
            result = solver.solve()
        else:
            # 动态加载候选策略
            try:
                module = __import__(f'strategies.strategy_{strategy}', fromlist=['Strategy'])
                solver = module.Strategy(configs)
                result = solver.solve()
            except ImportError:
                result = {'solve_status': 'error', 'message': f'策略 {strategy} 不存在'}

        # 保存结果到数据库
        self.db.save_schedule_result(
            self.current_batch_id,
            strategy,
            result.get('solve_status', 'unknown'),
            result.get('makespan', 0),
            result
        )

        return result

    def _generate_comparison_report(self, results: List[Dict]) -> Dict:
        """生成策略对比报告"""
        if not results:
            return {}

        # 找出最优策略
        valid_results = [r for r in results if r.get('solve_status') == 'optimal']
        if valid_results:
            best = min(valid_results, key=lambda x: x.get('makespan', float('inf')))
            best_strategy = best.get('strategy', 'unknown')
        else:
            best_strategy = None

        return {
            'best_strategy': best_strategy,
            'strategies_count': len(results),
            'comparison': [
                {
                    'strategy': r.get('strategy'),
                    'makespan': r.get('makespan'),
                    'solve_status': r.get('solve_status'),
                    'solve_time': r.get('solve_time')
                }
                for r in results
            ]
        }

    def pause_task(self, task_id: str) -> Dict:
        """
        接口5: 暂停任务
        返回: 操作结果
        """
        # TODO: 实现任务暂停逻辑
        self.db.log(self.current_batch_id, 'INFO', 'TASK_CONTROL',
                   f'暂停任务: {task_id}')
        return {'status': 'success', 'message': f'任务 {task_id} 已暂停'}

    def resume_task(self, task_id: str) -> Dict:
        """
        接口6: 恢复任务
        返回: 操作结果
        """
        # TODO: 实现任务恢复逻辑
        self.db.log(self.current_batch_id, 'INFO', 'TASK_CONTROL',
                   f'恢复任务: {task_id}')
        return {'status': 'success', 'message': f'任务 {task_id} 已恢复'}

    def add_emergency_task(self, task_data: Dict) -> Dict:
        """
        接口7: 添加紧急任务
        task_data: 紧急任务数据
        返回: 操作结果
        """
        try:
            task_data['task_type'] = 'emergency'
            task_data['priority'] = 1
            task_data['created_time'] = datetime.now().isoformat()

            # TODO: 实现紧急任务插入逻辑
            # 1. 备份并暂停所有非紧急任务
            # 2. 将紧急任务加入调度队列
            # 3. 触发重新调度

            self.db.log(self.current_batch_id, 'INFO', 'EMERGENCY',
                       f'添加紧急任务: {task_data.get("task_id")}')

            return {'status': 'success', 'message': '紧急任务已添加', 'task': task_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def confirm_emergency_completion(self, task_id: str) -> Dict:
        """
        接口8: 确认紧急任务完成
        返回: 操作结果
        """
        # TODO: 实现紧急任务完成确认逻辑
        # 恢复所有被暂停的非紧急任务

        self.db.log(self.current_batch_id, 'INFO', 'EMERGENCY',
                   f'确认紧急任务完成: {task_id}')

        return {'status': 'success', 'message': f'紧急任务 {task_id} 已确认完成，恢复其他任务'}

    # ==================== 查询接口 ====================

    def query_tasks(self, filters: Dict = None, page: int = 1,
                    page_size: int = 20, sort_by: str = 'created_at',
                    sort_order: str = 'desc') -> Dict:
        """
        接口9: 查询任务
        filters: 过滤条件（task_type, status, priority等）
        返回: 任务列表和分页信息
        """
        # TODO: 从任务配置和结果中查询
        return {
            'status': 'success',
            'data': [],
            'page': page,
            'page_size': page_size,
            'total': 0
        }

    def query_locomotives(self, filters: Dict = None, page: int = 1,
                          page_size: int = 20) -> Dict:
        """
        接口10: 查询机车
        返回: 机车列表和分页信息
        """
        # TODO: 从机车配置中查询
        return {
            'status': 'success',
            'data': [],
            'page': page,
            'page_size': page_size,
            'total': 0
        }

    def query_schedule_results(self, batch_id: str = None, strategy_name: str = None,
                               page: int = 1, page_size: int = 20) -> Dict:
        """
        接口11: 查询调度结果
        返回: 调度结果列表和分页信息
        """
        results, total = self.db.get_schedule_results(
            batch_id=batch_id,
            strategy_name=strategy_name,
            page=page,
            page_size=page_size
        )
        return {
            'status': 'success',
            'data': results,
            'page': page,
            'page_size': page_size,
            'total': total
        }

    def query_logs(self, batch_id: str = None, log_type: str = None,
                   log_level: str = None, page: int = 1, page_size: int = 20) -> Dict:
        """
        接口12: 查询日志
        返回: 日志列表和分页信息
        """
        logs, total = self.db.get_logs(
            batch_id=batch_id,
            log_type=log_type,
            log_level=log_level,
            page=page,
            page_size=page_size
        )
        return {
            'status': 'success',
            'data': logs,
            'page': page,
            'page_size': page_size,
            'total': total
        }

    def query_comparison_reports(self, batch_id: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict:
        """
        接口13: 查询策略对比报告
        返回: 对比报告列表和分页信息
        """
        reports, total = self.db.get_comparison_reports(
            batch_id=batch_id,
            page=page,
            page_size=page_size
        )
        return {
            'status': 'success',
            'data': reports,
            'page': page,
            'page_size': page_size,
            'total': total
        }

    # ==================== 导出接口 ====================

    def export_data(self, table_name: str, format: str = 'json',
                    batch_id: str = None) -> Dict:
        """
        接口14: 导出数据
        table_name: 要导出的表名
        format: json/csv
        返回: 导出的数据
        """
        try:
            if format == 'json':
                data = self.db.export_to_json(table_name, batch_id)
            elif format == 'csv':
                data = self.db.export_to_csv(table_name, batch_id)
            else:
                return {'status': 'error', 'message': f'不支持的格式: {format}'}

            return {
                'status': 'success',
                'data': data,
                'format': format,
                'filename': f'{table_name}_export.{format}'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # ==================== 统计接口 ====================

    def get_statistics(self) -> Dict:
        """
        接口15: 获取统计信息
        返回: 各策略的统计数据
        """
        try:
            stats = self.db.get_statistics()
            return {'status': 'success', 'data': stats}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # ==================== 能源管理接口 ====================

    def check_energy_status(self) -> Dict:
        """
        接口16: 检查机车能源状态
        返回: 各机车能源状态及报警信息
        """
        try:
            configs = self.load_configurations()
            if configs['status'] == 'error':
                return configs

            locos = configs['data']['locomotives_config'].get('locomotives', [])
            hyper_params = configs['data']['hyper_params']

            # 获取能源阈值
            electric_threshold = hyper_params.get('electric_energy_threshold', 20)
            diesel_threshold = hyper_params.get('diesel_fuel_threshold', 50)

            alerts = []
            status_list = []

            for loco in locos:
                loco_id = loco['loco_id']
                traction_type = loco['traction_type']

                if traction_type == 'electric':
                    battery = loco.get('battery', 0)
                    status_list.append({
                        'loco_id': loco_id,
                        'type': 'electric',
                        'energy_level': battery,
                        'unit': 'kWh'
                    })
                    if battery < electric_threshold:
                        alerts.append({
                            'loco_id': loco_id,
                            'type': 'low_battery',
                            'level': battery,
                            'threshold': electric_threshold,
                            'message': f'机车 {loco_id} 电量不足: {battery} kWh'
                        })

                elif traction_type == 'diesel':
                    fuel = loco.get('fuel_tank', 0)
                    status_list.append({
                        'loco_id': loco_id,
                        'type': 'diesel',
                        'energy_level': fuel,
                        'unit': 'L'
                    })
                    if fuel < diesel_threshold:
                        alerts.append({
                            'loco_id': loco_id,
                            'type': 'low_fuel',
                            'level': fuel,
                            'threshold': diesel_threshold,
                            'message': f'机车 {loco_id} 油量不足: {fuel} L'
                        })

            return {
                'status': 'success',
                'data': {
                    'energy_status': status_list,
                    'alerts': alerts,
                    'alert_count': len(alerts)
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def close(self):
        """关闭数据库连接"""
        self.db.close()


if __name__ == '__main__':
    # 测试API
    api = ScheduleAPI()
    print("ScheduleAPI 初始化成功")
    print(f"共提供 {16} 个API接口")

    # 测试统计接口
    stats = api.get_statistics()
    print(f"统计信息: {stats}")

    api.close()