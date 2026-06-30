"""
车辆调度AI算法评测系统 - 数据库模块
使用SQLite数据库，包含7张表的CRUD操作
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import os


class ScheduleDatabase:
    """调度历史数据库 - SQLite版本"""

    def __init__(self, db_path: str = 'database/schedule_history.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = None
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. 地图配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                config_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. 任务配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                config_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 机车配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locomotives_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                config_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 4. 超参数配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hyper_params_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                config_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 5. 调度结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                solve_status TEXT NOT NULL,
                makespan REAL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 6. 系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                log_level TEXT NOT NULL,
                log_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 7. 策略对比表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparison_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                strategies TEXT NOT NULL,
                best_strategy TEXT,
                comparison_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_map_batch ON map_configs(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_batch ON tasks_configs(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loco_batch ON locomotives_configs(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hyper_batch ON hyper_params_configs(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_batch ON schedule_results(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_strategy ON schedule_results(strategy_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_batch ON system_logs(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_type ON system_logs(log_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparison_batch ON comparison_reports(batch_id)')

        conn.commit()

    # ==================== 配置存储 ====================

    def save_map_config(self, batch_id: str, config: Dict) -> int:
        """保存地图配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO map_configs (batch_id, config_json) VALUES (?, ?)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        return cursor.lastrowid

    def save_tasks_config(self, batch_id: str, config: Dict) -> int:
        """保存任务配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks_configs (batch_id, config_json) VALUES (?, ?)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        return cursor.lastrowid

    def save_locomotives_config(self, batch_id: str, config: Dict) -> int:
        """保存机车配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO locomotives_configs (batch_id, config_json) VALUES (?, ?)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        return cursor.lastrowid

    def save_hyper_params(self, batch_id: str, config: Dict) -> int:
        """保存超参数配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO hyper_params_configs (batch_id, config_json) VALUES (?, ?)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        return cursor.lastrowid

    # ==================== 调度结果 ====================

    def save_schedule_result(self, batch_id: str, strategy_name: str,
                             solve_status: str, makespan: float, result: Dict) -> int:
        """保存调度结果"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO schedule_results
               (batch_id, strategy_name, solve_status, makespan, result_json)
               VALUES (?, ?, ?, ?, ?)''',
            (batch_id, strategy_name, solve_status, makespan,
             json.dumps(result, ensure_ascii=False))
        )
        conn.commit()
        return cursor.lastrowid

    def get_schedule_results(self, batch_id: str = None, strategy_name: str = None,
                             page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """
        查询调度结果（支持分页）
        返回: (结果列表, 总数)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []
        if batch_id:
            conditions.append('batch_id = ?')
            params.append(batch_id)
        if strategy_name:
            conditions.append('strategy_name = ?')
            params.append(strategy_name)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        cursor.execute(f'SELECT COUNT(*) FROM schedule_results WHERE {where_clause}', params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(
            f'''SELECT * FROM schedule_results WHERE {where_clause}
                ORDER BY created_at DESC LIMIT ? OFFSET ?''',
            params + [page_size, offset]
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'batch_id': row['batch_id'],
                'strategy_name': row['strategy_name'],
                'solve_status': row['solve_status'],
                'makespan': row['makespan'],
                'result': json.loads(row['result_json']),
                'created_at': row['created_at']
            })

        return results, total

    # ==================== 日志记录 ====================

    def log(self, batch_id: str, log_level: str, log_type: str,
            message: str, details: Dict = None):
        """记录日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO system_logs
               (batch_id, log_level, log_type, message, details)
               VALUES (?, ?, ?, ?, ?)''',
            (batch_id, log_level, log_type, message,
             json.dumps(details, ensure_ascii=False) if details else None)
        )
        conn.commit()

    def get_logs(self, batch_id: str = None, log_type: str = None,
                 log_level: str = None, page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """查询日志（支持分页）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []
        if batch_id:
            conditions.append('batch_id = ?')
            params.append(batch_id)
        if log_type:
            conditions.append('log_type = ?')
            params.append(log_type)
        if log_level:
            conditions.append('log_level = ?')
            params.append(log_level)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        cursor.execute(f'SELECT COUNT(*) FROM system_logs WHERE {where_clause}', params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(
            f'''SELECT * FROM system_logs WHERE {where_clause}
                ORDER BY created_at DESC LIMIT ? OFFSET ?''',
            params + [page_size, offset]
        )

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'batch_id': row['batch_id'],
                'log_level': row['log_level'],
                'log_type': row['log_type'],
                'message': row['message'],
                'details': json.loads(row['details']) if row['details'] else None,
                'created_at': row['created_at']
            })

        return logs, total

    # ==================== 策略对比 ====================

    def save_comparison_report(self, batch_id: str, strategies: List[str],
                               best_strategy: str, comparison: Dict) -> int:
        """保存策略对比报告"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO comparison_reports
               (batch_id, strategies, best_strategy, comparison_json)
               VALUES (?, ?, ?, ?)''',
            (batch_id, json.dumps(strategies), best_strategy,
             json.dumps(comparison, ensure_ascii=False))
        )
        conn.commit()
        return cursor.lastrowid

    def get_comparison_reports(self, batch_id: str = None,
                               page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """查询策略对比报告（支持分页）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if batch_id:
            cursor.execute('SELECT COUNT(*) FROM comparison_reports WHERE batch_id = ?', (batch_id,))
            total = cursor.fetchone()[0]
            cursor.execute(
                '''SELECT * FROM comparison_reports WHERE batch_id = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?''',
                (batch_id, page_size, (page - 1) * page_size)
            )
        else:
            cursor.execute('SELECT COUNT(*) FROM comparison_reports')
            total = cursor.fetchone()[0]
            cursor.execute(
                '''SELECT * FROM comparison_reports
                   ORDER BY created_at DESC LIMIT ? OFFSET ?''',
                (page_size, (page - 1) * page_size)
            )

        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': row['id'],
                'batch_id': row['batch_id'],
                'strategies': json.loads(row['strategies']),
                'best_strategy': row['best_strategy'],
                'comparison': json.loads(row['comparison_json']),
                'created_at': row['created_at']
            })

        return reports, total

    # ==================== 统计信息 ====================

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*) FROM schedule_results')
        stats['total_results'] = cursor.fetchone()[0]

        cursor.execute('''
            SELECT strategy_name, COUNT(*) as count, AVG(makespan) as avg_makespan
            FROM schedule_results
            GROUP BY strategy_name
        ''')
        stats['strategy_stats'] = []
        for row in cursor.fetchall():
            stats['strategy_stats'].append({
                'strategy_name': row[0],
                'count': row[1],
                'avg_makespan': row[2]
            })

        cursor.execute('''
            SELECT strategy_name, COUNT(*) as best_count
            FROM (
                SELECT batch_id, strategy_name, makespan,
                       RANK() OVER (PARTITION BY batch_id ORDER BY makespan) as rk
                FROM schedule_results
                WHERE solve_status = 'optimal'
            )
            WHERE rk = 1
            GROUP BY strategy_name
        ''')
        stats['best_count'] = []
        for row in cursor.fetchall():
            stats['best_count'].append({
                'strategy_name': row[0],
                'best_count': row[1]
            })

        return stats

    # ==================== 导出功能 ====================

    def export_to_json(self, table_name: str, batch_id: str = None) -> str:
        """导出数据为JSON格式"""
        valid_tables = ['map_configs', 'tasks_configs', 'locomotives_configs',
                        'hyper_params_configs', 'schedule_results', 'system_logs',
                        'comparison_reports']
        if table_name not in valid_tables:
            raise ValueError(f"无效的表名: {table_name}")

        conn = self._get_connection()
        cursor = conn.cursor()

        if batch_id:
            cursor.execute(f'SELECT * FROM {table_name} WHERE batch_id = ?', (batch_id,))
        else:
            cursor.execute(f'SELECT * FROM {table_name}')

        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def export_to_csv(self, table_name: str, batch_id: str = None) -> str:
        """导出数据为CSV格式"""
        import csv
        import io

        valid_tables = ['map_configs', 'tasks_configs', 'locomotives_configs',
                        'hyper_params_configs', 'schedule_results', 'system_logs',
                        'comparison_reports']
        if table_name not in valid_tables:
            raise ValueError(f"无效的表名: {table_name}")

        conn = self._get_connection()
        cursor = conn.cursor()

        if batch_id:
            cursor.execute(f'SELECT * FROM {table_name} WHERE batch_id = ?', (batch_id,))
        else:
            cursor.execute(f'SELECT * FROM {table_name}')

        rows = cursor.fetchall()
        if not rows:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(rows[0].keys())

        for row in rows:
            writer.writerow(row.values())

        return output.getvalue()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


if __name__ == '__main__':
    db = ScheduleDatabase()
    print("SQLite数据库初始化成功")
    stats = db.get_statistics()
    print(f"统计信息: {stats}")
    db.close()