// 车辆调度AI算法评测系统 - JavaScript文件

// API基础路径
const API_BASE = '/api';

// 加载配置
async function loadConfigs() {
    try {
        const response = await fetch(`${API_BASE}/load`);
        const data = await response.json();
        if (data.status === 'success') {
            alert('配置加载成功');
            updateStatus(data.data);
        } else {
            alert('配置加载失败: ' + data.message);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }
}

// 执行调度
async function executeScheduling() {
    try {
        const response = await fetch(`${API_BASE}/execute`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({strategy: 'baseline'})
        });
        const data = await response.json();
        if (data.status === 'success') {
            alert('调度执行成功\n批次ID: ' + data.batch_id);
        } else {
            alert('调度执行失败: ' + data.message);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }
}

// 策略对比
async function compareStrategies() {
    try {
        const response = await fetch(`${API_BASE}/execute`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                strategies: ['baseline', 'strategy1', 'strategy2'],
                compare_mode: true
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            alert('策略对比执行成功');
            // 跳转到对比结果页面
            window.location.href = '/comparison?batch_id=' + data.batch_id;
        } else {
            alert('策略对比执行失败: ' + data.message);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }
}

// 添加紧急任务
function addEmergencyTask() {
    // 跳转到紧急任务添加页面
    window.location.href = '/scheduling?action=emergency';
}

// 更新状态显示
function updateStatus(data) {
    if (data.locomotives_config) {
        const available = data.locomotives_config.locomotives.filter(
            l => l.is_powered_on && l.is_schedulable
        ).length;
        document.getElementById('available_locos').textContent = available;
    }

    if (data.tasks_config) {
        const pending = data.tasks_config.tasks.filter(
            t => t.status === 'running'
        ).length;
        document.getElementById('pending_tasks').textContent = pending;

        const emergency = data.tasks_config.tasks.filter(
            t => t.task_type === 'emergency'
        ).length;
        document.getElementById('emergency_tasks').textContent = emergency;
    }
}

// 分页查询
async function queryData(type, page = 1, pageSize = 20) {
    try {
        const response = await fetch(
            `${API_BASE}/query/${type}?page=${page}&pageSize=${pageSize}`
        );
        const data = await response.json();
        if (data.status === 'success') {
            return data;
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('查询失败:', error);
        return null;
    }
}

// 导出数据
async function exportData(table, format = 'json') {
    try {
        const response = await fetch(`${API_BASE}/export/${table}?format=${format}`);
        const data = await response.json();
        if (data.status === 'success') {
            // 创建下载链接
            const blob = new Blob([data.data], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename;
            a.click();
        } else {
            alert('导出失败: ' + data.message);
        }
    } catch (error) {
        alert('导出失败: ' + error.message);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 自动加载状态
    loadConfigs();
});