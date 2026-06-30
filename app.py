"""
车辆调度AI算法评测系统 - Flask应用入口
运行方式: python app.py
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import json

# 导入核心模块
from schedule_api import ScheduleAPI

app = Flask(__name__)
CORS(app)

app.config['JSON_AS_ASCII'] = False

api = None


def get_api():
    """获取API实例"""
    global api
    if api is None:
        api = ScheduleAPI()
    return api


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/config/map')
def map_config():
    """地图配置页面"""
    return render_template('config/map_config.html')


@app.route('/config/tasks')
def tasks_config():
    """任务配置页面"""
    return render_template('config/tasks_config.html')


@app.route('/config/locomotives')
def locomotives_config():
    """机车配置页面"""
    return render_template('config/locomotives_config.html')


@app.route('/config/hyper')
def hyper_config():
    """超参数配置页面"""
    return render_template('config/hyper_params.html')


@app.route('/scheduling')
def scheduling():
    """调度控制页面"""
    action = request.args.get('action', '')
    return render_template('scheduling/scheduling.html', action=action)


@app.route('/comparison')
def comparison():
    """策略对比页面"""
    batch_id = request.args.get('batch_id', '')
    return render_template('comparison/comparison.html', batch_id=batch_id)


@app.route('/query')
def query():
    """数据查询页面"""
    return render_template('query/query.html')


# ==================== API接口 ====================

@app.route('/api/load', methods=['GET'])
def api_load_configurations():
    """加载所有配置文件"""
    try:
        schedule_api = get_api()
        result = schedule_api.load_configurations()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/save', methods=['POST'])
def api_save_configuration():
    """保存配置文件"""
    try:
        data = request.get_json()
        config_type = data.get('config_type')
        config_data = data.get('config_data')

        schedule_api = get_api()
        result = schedule_api.save_configuration(config_type, config_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/validate', methods=['POST'])
def api_validate_configuration():
    """验证配置数据"""
    try:
        data = request.get_json()
        config_type = data.get('config_type')
        config_data = data.get('config_data')

        schedule_api = get_api()
        result = schedule_api.validate_configuration(config_type, config_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/execute', methods=['POST'])
def api_execute_scheduling():
    """执行调度"""
    try:
        data = request.get_json()
        strategies = data.get('strategies', ['baseline'])
        compare_mode = data.get('compare_mode', False)

        schedule_api = get_api()
        result = schedule_api.execute_scheduling(strategies, compare_mode)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/pause', methods=['POST'])
def api_pause_task():
    """暂停任务"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')

        schedule_api = get_api()
        result = schedule_api.pause_task(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/resume', methods=['POST'])
def api_resume_task():
    """恢复任务"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')

        schedule_api = get_api()
        result = schedule_api.resume_task(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/emergency', methods=['POST'])
def api_add_emergency_task():
    """添加紧急任务"""
    try:
        data = request.get_json()
        task_data = data.get('task_data')

        schedule_api = get_api()
        result = schedule_api.add_emergency_task(task_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/emergency/confirm', methods=['POST'])
def api_confirm_emergency():
    """确认紧急任务完成"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')

        schedule_api = get_api()
        result = schedule_api.confirm_emergency_completion(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/query/tasks', methods=['GET'])
def api_query_tasks():
    """查询任务"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        schedule_api = get_api()
        result = schedule_api.query_tasks(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/query/locomotives', methods=['GET'])
def api_query_locomotives():
    """查询机车"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        schedule_api = get_api()
        result = schedule_api.query_locomotives(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/query/results', methods=['GET'])
def api_query_results():
    """查询调度结果"""
    try:
        batch_id = request.args.get('batch_id')
        strategy_name = request.args.get('strategy_name')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        schedule_api = get_api()
        result = schedule_api.query_schedule_results(
            batch_id=batch_id,
            strategy_name=strategy_name,
            page=page,
            page_size=page_size
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/query/logs', methods=['GET'])
def api_query_logs():
    """查询日志"""
    try:
        batch_id = request.args.get('batch_id')
        log_type = request.args.get('log_type')
        log_level = request.args.get('log_level')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        schedule_api = get_api()
        result = schedule_api.query_logs(
            batch_id=batch_id,
            log_type=log_type,
            log_level=log_level,
            page=page,
            page_size=page_size
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/query/comparison', methods=['GET'])
def api_query_comparison():
    """查询策略对比报告"""
    try:
        batch_id = request.args.get('batch_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        schedule_api = get_api()
        result = schedule_api.query_comparison_reports(
            batch_id=batch_id,
            page=page,
            page_size=page_size
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/export', methods=['GET'])
def api_export_data():
    """导出数据"""
    try:
        table_name = request.args.get('table_name')
        format_type = request.args.get('format', 'json')
        batch_id = request.args.get('batch_id')

        schedule_api = get_api()
        result = schedule_api.export_data(table_name, format_type, batch_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    """获取统计信息"""
    try:
        schedule_api = get_api()
        result = schedule_api.get_statistics()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/energy', methods=['GET'])
def api_check_energy():
    """检查能源状态"""
    try:
        schedule_api = get_api()
        result = schedule_api.check_energy_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/configs/map', methods=['GET'])
def api_get_map_config():
    """获取地图配置"""
    config_path = os.path.join('configs', 'map_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/api/configs/tasks', methods=['GET'])
def api_get_tasks_config():
    """获取任务配置"""
    config_path = os.path.join('configs', 'tasks_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/api/configs/locomotives', methods=['GET'])
def api_get_locomotives_config():
    """获取机车配置"""
    config_path = os.path.join('configs', 'locomotives_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/api/configs/hyper', methods=['GET'])
def api_get_hyper_config():
    """获取超参数配置"""
    config_path = os.path.join('configs', 'hyper_params.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/api/configs', methods=['PUT'])
def api_update_config():
    """更新配置文件"""
    try:
        data = request.get_json()
        config_type = data.get('config_type')
        config_data = data.get('config_data')

        filename_map = {
            'map': 'map_config.json',
            'tasks': 'tasks_config.json',
            'locomotives': 'locomotives_config.json',
            'hyper': 'hyper_params.json'
        }

        if config_type not in filename_map:
            return jsonify({'status': 'error', 'message': '无效的配置类型'})

        filepath = os.path.join('configs', filename_map[config_type])
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        return jsonify({'status': 'success', 'message': f'{config_type}配置已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    print("=" * 60)
    print("车辆调度AI算法评测系统")
    print("启动中...")
    print("=" * 60)

    try:
        api = ScheduleAPI()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        print("请检查数据库文件路径是否正确")
        exit(1)

    print("\n启动Flask服务...")
    print("访问地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)