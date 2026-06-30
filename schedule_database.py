"""
车辆调度AI算法评测系统 - 数据库模块
使用MySQL数据库，包含7张表的CRUD操作
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import mysql.connector
from mysql.connector import Error


class ScheduleDatabase:
    """调度历史数据库 - MySQL版本"""

    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = 'root', password: str = '123456',
                 database: str = 'vehicle_scheduling'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self._init_database()

    def _get_connection(self):
        """获取数据库连接"""
        if self.conn is None or not self.conn.is_connected():
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
        return self.conn

    def _init_database(self):
        """初始化数据库和表结构"""
        # 先连接MySQL服务器，创建数据库
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()

        # 连接到指定数据库，创建表
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. 地图配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_configs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100) NOT NULL,
                config_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_map_batch (batch_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # 2. 任务配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks_configs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100) NOT NULL,
                config_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tasks_batch (batch_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # 3. 机车配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locomotives_configs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100) NOT NULL,
                config_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_loco_batch (batch_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # 4. 超参数配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hyper_params_configs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100) NOT NULL,
                config_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_hyper_batch (batch_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # 5. 调度结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_results (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100) NOT NULL,
                strategy_name VARCHAR(100) NOT NULL,
                solve_status VARCHAR(50) NOT NULL,
                makespan DOUBLE,
                result_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_results_batch (batch_id),
                INDEX idx_results_strategy (strategy_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # 6. 系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100),
                log_level VARCHAR(20) NOT NULL,
                log_type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_logs_batch (batch_id),
                INDEX idx_logs_type (log_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # 7. 策略对比表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparison_reports (
                id INT PRIMARY KEY AUTO_INCREMENT,
                batch_id VARCHAR(100) NOT NULL,
                strategies JSON NOT NULL,
                best_strategy VARCHAR(100),
                comparison_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_comparison_batch (batch_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        conn.commit()
        cursor.close()

    # ==================== 配置存储 ====================

    def save_map_config(self, batch_id: str, config: Dict) -> int:
        """保存地图配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO map_configs (batch_id, config_json) VALUES (%s, %s)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def save_tasks_config(self, batch_id: str, config: Dict) -> int:
        """保存任务配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks_configs (batch_id, config_json) VALUES (%s, %s)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def save_locomotives_config(self, batch_id: str, config: Dict) -> int:
        """保存机车配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO locomotives_configs (batch_id, config_json) VALUES (%s, %s)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def save_hyper_params(self, batch_id: str, config: Dict) -> int:
        """保存超参数配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO hyper_params_configs (batch_id, config_json) VALUES (%s, %s)',
            (batch_id, json.dumps(config, ensure_ascii=False))
        )
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    # ==================== 调度结果 ====================

    def save_schedule_result(self, batch_id: str, strategy_name: str,
                             solve_status: str, makespan: float, result: Dict) -> int:
        """保存调度结果"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO schedule_results
               (batch_id, strategy_name, solve_status, makespan, result_json)
               VALUES (%s, %s, %s, %s, %s)''',
            (batch_id, strategy_name, solve_status, makespan,
             json.dumps(result, ensure_ascii=False))
        )
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def get_schedule_results(self, batch_id: str = None, strategy_name: str = None,
                             page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """
        查询调度结果（支持分页）
        返回: (结果列表, 总数)
        """
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []
        if batch_id:
            conditions.append('batch_id = %s')
            params.append(batch_id)
        if strategy_name:
            conditions.append('strategy_name = %s')
            params.append(strategy_name)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        cursor.execute(f'SELECT COUNT(*) as cnt FROM schedule_results WHERE {where_clause}', params)
        total = cursor.fetchone()['cnt']

        offset = (page - 1) * page_size
        cursor.execute(
            f'''SELECT * FROM schedule_results WHERE {where_clause}
                ORDER BY created_at DESC LIMIT %s OFFSET %s''',
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
                'result': json.loads(row['result_json']) if isinstance(row['result_json'], str) else row['result_json'],
                'created_at': str(row['created_at']) if row['created_at'] else None
            })

        cursor.close()
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
               VALUES (%s, %s, %s, %s, %s)''',
            (batch_id, log_level, log_type, message,
             json.dumps(details, ensure_ascii=False) if details else None)
        )
        conn.commit()
        cursor.close()

    def get_logs(self, batch_id: str = None, log_type: str = None,
                 log_level: str = None, page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """查询日志（支持分页）"""
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []
        if batch_id:
            conditions.append('batch_id = %s')
            params.append(batch_id)
        if log_type:
            conditions.append('log_type = %s')
            params.append(log_type)
        if log_level:
            conditions.append('log_level = %s')
            params.append(log_level)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        cursor.execute(f'SELECT COUNT(*) as cnt FROM system_logs WHERE {where_clause}', params)
        total = cursor.fetchone()['cnt']

        offset = (page - 1) * page_size
        cursor.execute(
            f'''SELECT * FROM system_logs WHERE {where_clause}
                ORDER BY created_at DESC LIMIT %s OFFSET %s''',
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
                'details': json.loads(row['details']) if row['details'] and isinstance(row['details'], str) else row['details'],
                'created_at': str(row['created_at']) if row['created_at'] else None
            })

        cursor.close()
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
               VALUES (%s, %s, %s, %s)''',
            (batch_id, json.dumps(strategies), best_strategy,
             json.dumps(comparison, ensure_ascii=False))
        )
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def get_comparison_reports(self, batch_id: str = None,
                               page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """查询策略对比报告（支持分页）"""
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)

        if batch_id:
            cursor.execute('SELECT COUNT(*) as cnt FROM comparison_reports WHERE batch_id = %s', (batch_id,))
            total = cursor.fetchone()['cnt']
            cursor.execute(
                '''SELECT * FROM comparison_reports WHERE batch_id = %s
                   ORDER BY created_at DESC LIMIT %s OFFSET %s''',
                (batch_id, page_size, (page - 1) * page_size)
            )
        else:
            cursor.execute('SELECT COUNT(*) as cnt FROM comparison_reports')
            total = cursor.fetchone()['cnt']
            cursor.execute(
                '''SELECT * FROM comparison_reports
                   ORDER BY created_at DESC LIMIT %s OFFSET %s''',
                (page_size, (page - 1) * page_size)
            )

        reports = []
        for row in cursor.fetchall():
            strategies_data = row['strategies']
            if isinstance(strategies_data, str):
                strategies_data = json.loads(strategies_data)
            comparison_data = row['comparison_json']
            if isinstance(comparison_data, str):
                comparison_data = json.loads(comparison_data)
            reports.append({
                'id': row['id'],
                'batch_id': row['batch_id'],
                'strategies': strategies_data,
                'best_strategy': row['best_strategy'],
                'comparison': comparison_data,
                'created_at': str(row['created_at']) if row['created_at'] else None
            })

        cursor.close()
        return reports, total

    # ==================== 统计信息 ====================

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)

        stats = {}

        cursor.execute('SELECT COUNT(*) as cnt FROM schedule_results')
        stats['total_results'] = cursor.fetchone()['cnt']

        cursor.execute('''
            SELECT strategy_name, COUNT(*) as count, AVG(makespan) as avg_makespan
            FROM schedule_results
            GROUP BY strategy_name
        ''')
        stats['strategy_stats'] = []
        for row in cursor.fetchall():
            stats['strategy_stats'].append({
                'strategy_name': row['strategy_name'],
                'count': row['count'],
                'avg_makespan': float(row['avg_makespan']) if row['avg_makespan'] else 0
            })

        cursor.execute('''
            SELECT strategy_name, COUNT(*) as best_count
            FROM (
                SELECT batch_id, strategy_name, makespan,
                       RANK() OVER (PARTITION BY batch_id ORDER BY makespan) as rk
                FROM schedule_results
                WHERE solve_status = 'optimal'
            ) t
            WHERE rk = 1
            GROUP BY strategy_name
        ''')
        stats['best_count'] = []
        for row in cursor.fetchall():
            stats['best_count'].append({
                'strategy_name': row['strategy_name'],
                'best_count': row['best_count']
            })

        cursor.close()
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
        cursor = conn.cursor(dictionary=True)

        if batch_id:
            cursor.execute(f'SELECT * FROM {table_name} WHERE batch_id = %s', (batch_id,))
        else:
            cursor.execute(f'SELECT * FROM {table_name}')

        rows = cursor.fetchall()
        data = []
        for row in rows:
            row_dict = {}
            for k, v in row.items():
                if isinstance(v, (datetime,)):
                    row_dict[k] = str(v)
                else:
                    row_dict[k] = v
            data.append(row_dict)
        cursor.close()
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
        cursor = conn.cursor(dictionary=True)

        if batch_id:
            cursor.execute(f'SELECT * FROM {table_name} WHERE batch_id = %s', (batch_id,))
        else:
            cursor.execute(f'SELECT * FROM {table_name}')

        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            return ""

        output = io.StringIO()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row_dict = {}
            for k, v in row.items():
                if isinstance(v, (datetime,)):
                    row_dict[k] = str(v)
                else:
                    row_dict[k] = v
            writer.writerow(row_dict)

        return output.getvalue()

    def close(self):
        """关闭数据库连接"""
        if self.conn and self.conn.is_connected():
            self.conn.close()
            self.conn = None


if __name__ == '__main__':
    db = ScheduleDatabase()
    print("MySQL数据库初始化成功")
    stats = db.get_statistics()
    print(f"统计信息: {stats}")
    db.close()