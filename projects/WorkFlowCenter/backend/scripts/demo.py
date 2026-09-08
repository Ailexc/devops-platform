#!/usr/bin/env python
"""
演示脚本：自动跑通完整流程

用法:
  cd backend
  python scripts/demo.py

前置条件:
  1. docker compose up (启动服务)
  2. python manage.py seed_data (初始化种子数据)
"""
import sys
import os
import time
import json
import requests

BASE_URL = os.environ.get('API_URL', 'http://api.workflow.orb.local/api/v1')


def login(username, password):
    """登录获取 JWT token"""
    resp = requests.post(f'{BASE_URL}/auth/token/', json={
        'username': username,
        'password': password,
    })
    resp.raise_for_status()
    data = resp.json()
    return data['access']


def get_headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def demo_complete_flow():
    """演示完整流程"""
    print('=' * 60)
    print('  工单系统 Demo - 完整流程演示')
    print('=' * 60)

    # 1. 用户登录
    print('\n[1] 用户登录 (user1)')
    token = login('user1', 'user123')
    headers = get_headers(token)
    print('  ✓ 登录成功')

    # 2. 查看可用流程定义
    print('\n[2] 查看可用流程模版')
    resp = requests.get(f'{BASE_URL}/process-definitions/', headers=headers)
    definitions = resp.json().get('results', resp.json())
    if isinstance(definitions, dict):
        definitions = definitions.get('results', [])
    for d in definitions:
        print(f'  - {d["name"]} ({d["key"]}) v{d["version"]} [{d["status"]}]')

    # 3. 发起工单
    print('\n[3] 发起工单 - 服务器申请')
    resp = requests.post(f'{BASE_URL}/process-instances/start/', headers=headers, json={
        'definition_id': definitions[0]['id'],
        'form_data': {
            'hostname': 'web-server-001',
            'cpu': 8,
            'memory': 16,
            'os': 'Ubuntu 22.04',
            'amount': 5000,
            'reason': '业务扩容需要',
            'email': 'user1@example.com',
        },
    })
    resp.raise_for_status()
    instance = resp.json()
    instance_id = instance['id']
    print(f'  ✓ 工单创建成功: {instance["instance_no"]}')
    print(f'  实例 ID: {instance_id}')

    # 4. 查看待办任务
    print('\n[4] agent1 查看待办任务')
    agent_token = login('agent1', 'agent123')
    agent_headers = get_headers(agent_token)
    resp = requests.get(f'{BASE_URL}/node-tasks/?status=pending', headers=agent_headers)
    tasks = resp.json().get('results', resp.json())
    if isinstance(tasks, dict):
        tasks = tasks.get('results', [])
    print(f'  待办任务数: {len(tasks)}')
    for t in tasks:
        print(f'  - #{t["id"]} {t["node_name"]} [{t["status"]}]')

    # 5. 签收并完成任务
    if tasks:
        task = tasks[0]
        print(f'\n[5] 签收任务 #{task["id"]}')
        resp = requests.post(f'{BASE_URL}/node-tasks/{task["id"]}/claim/', headers=agent_headers)
        if resp.status_code < 300:
            print('  ✓ 签收成功')
        else:
            print(f'  签收结果: {resp.status_code} {resp.text[:200]}')

        print(f'\n[6] 审批任务 #{task["id"]} - 同意')
        resp = requests.post(f'{BASE_URL}/node-tasks/{task["id"]}/complete/', headers=agent_headers, json={
            'result': 'approve',
            'opinion': '同意，资源充足',
        })
        if resp.status_code < 300:
            print('  ✓ 审批通过')
        else:
            print(f'  审批结果: {resp.status_code} {resp.text[:200]}')

    # 6. 查看实例状态
    print('\n[7] 查看流程实例状态')
    resp = requests.get(f'{BASE_URL}/process-instances/{instance_id}/', headers=headers)
    inst = resp.json()
    print(f'  状态: {inst["status"]}')
    print(f'  当前节点: {inst["current_node_key"]}')

    # 7. 查看审批记录
    print('\n[8] 查看审批记录')
    resp = requests.get(f'{BASE_URL}/process-instances/{instance_id}/approval-records/', headers=headers)
    records = resp.json()
    if isinstance(records, dict):
        records = records.get('results', [])
    for r in records:
        print(f'  - {r.get("user_name", "系统")} {r["action"]}: {r.get("opinion", "")}')

    # 8. 查看事件日志
    print('\n[9] 查看事件日志')
    resp = requests.get(f'{BASE_URL}/events/?instance={instance_id}', headers=headers)
    events = resp.json().get('results', resp.json())
    if isinstance(events, dict):
        events = events.get('results', [])
    for e in events:
        print(f'  - {e["type"]} @ {e.get("created_at", "")[:19]}')

    print('\n' + '=' * 60)
    print('  演示完成！')
    print('=' * 60)


if __name__ == '__main__':
    try:
        demo_complete_flow()
    except requests.ConnectionError:
        print('错误: 无法连接到后端服务。请确保 docker compose up 已启动。')
        sys.exit(1)
    except Exception as e:
        print(f'演示出错: {e}')
        sys.exit(1)
