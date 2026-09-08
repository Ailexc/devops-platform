"""
AI 表单生成服务

基于 OpenAI 兼容的 chat/completions 接口，将自然语言指令转换为
form-create 规则（与前端 FormBuilder 兼容的 form_schema）。
"""
import json
import logging
import re
import urllib.request
import urllib.error

from django.conf import settings

from apps.common.models import AIConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 提示词
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """你是一个表单设计专家。根据用户的自然语言描述，生成一个表单的 JSON Schema。

要求：
1. 输出必须是严格的 JSON，不要包含任何解释文字、Markdown 代码块标记或注释。
2. JSON 结构必须为 form-create 兼容格式：
{
  "rules": [
    {
      "type": "input",
      "field": "name",
      "title": "姓名",
      "value": "",
      "props": { "placeholder": "请输入姓名", "clearable": true }
    }
  ],
  "options": { "form": { "labelWidth": "120px" } }
}

支持的组件类型（type）：
- input: 单行文本（field: 英文字段名，title: 中文标签）
- textarea: 多行文本
- inputNumber: 数字
- money: 金额（可使用 input-number 或自定义）
- radio: 单选（options 为 [{value,label}] 或字符串数组）
- checkbox: 多选
- select: 下拉选择（options 为 [{value,label}]）
- date: 日期
- time: 时间
- switch: 开关（value 为布尔值）
- rate: 评分
- slider: 滑动条
- cascader: 级联选择

字段规则：
- field 必须是英文字段名（字母开头，可含数字和下划线）
- 必填字段使用 validate: [{ required: true, message: "xxx", trigger: "blur" }]
- 根据字段类型选择合适的校验（数字校验数字、邮箱校验邮箱等）
- 组件属性放在 props 中（如 placeholder、maxlength、rows、step 等）
- 需要选项的组件必须提供合理的选项值（中文场景）
- 合理设置表单布局：通常包含 3-10 个字段

请生成贴合用户需求、字段合理、校验完整的表单。"""


class AIServiceError(Exception):
    """AI 服务异常"""


def _extract_json(text: str) -> dict:
    """从模型输出中提取 JSON"""
    # 去掉可能的 markdown 代码块
    text = text.strip()
    code_block = re.search(r'```(?:json)?\s*(.*?)```', text, re.S)
    if code_block:
        text = code_block.group(1).strip()
    # 定位第一个 { 和最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise AIServiceError('模型输出中未找到有效的 JSON')
    return json.loads(text[start:end + 1])


def _normalize_schema(data: dict) -> dict:
    """规范化生成的表单 Schema，确保与前端兼容"""
    rules = data.get('rules') or []
    normalized = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        field = rule.get('field') or rule.get('name')
        if not field:
            continue
        rtype = rule.get('type')
        title = rule.get('title') or rule.get('label') or field
        new_rule = {
            'type': rtype,
            'field': field,
            'title': title,
            'value': rule.get('value'),
        }
        if rule.get('props'):
            new_rule['props'] = rule['props']
        if rule.get('validate'):
            new_rule['validate'] = rule['validate']
        # 选项字段
        options = rule.get('options')
        if options:
            if isinstance(options, list) and options and isinstance(options[0], dict):
                new_rule['options'] = options
            elif isinstance(options, list):
                new_rule['options'] = options
        normalized.append(new_rule)

    return {
        'rules': normalized,
        'options': data.get('options') or {'form': {'labelWidth': '120px'}},
    }


def generate_form(config: AIConfig, prompt: str) -> dict:
    """调用 AI 生成表单 Schema

    Args:
        config: AIConfig 实例（可为未保存的临时对象）
        prompt: 用户的自然语言描述

    Returns:
        {"form_schema": {"rules": [...], "options": {}}, "raw": "..."}
    """
    api_base = config.effective_api_base()
    api_key = config.effective_api_key()
    model_id = config.effective_model_id()

    if not api_base:
        raise AIServiceError(f'提供商「{config.get_provider_display()}」未配置 API 端点')
    if not api_key:
        raise AIServiceError(
            f'提供商「{config.get_provider_display()}」未配置 API Key，'
            f'请在环境变量中设置 {config.api_key_env_name()}'
        )

    body = {
        'model': model_id,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'请为以下需求生成表单：\n{prompt}'},
        ],
        'temperature': 0.3,
        'response_format': {'type': 'json_object'},
    }

    headers = {
        'Content-Type': 'application/json',
    }
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    req = urllib.request.Request(
        api_base,
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method='POST',
    )

    timeout = getattr(settings, 'AI_REQUEST_TIMEOUT', 60)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='ignore')[:500]
        logger.error('AI 请求失败: %s %s', e.code, detail)
        raise AIServiceError(f'AI 服务返回错误（{e.code}）: {detail}')
    except urllib.error.URLError as e:
        logger.error('AI 连接失败: %s', e.reason)
        raise AIServiceError(f'无法连接 AI 服务: {e.reason}')
    except Exception as e:
        logger.error('AI 请求异常: %s', e)
        raise AIServiceError(f'AI 请求异常: {e}')

    # 解析响应
    try:
        content = payload['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise AIServiceError('AI 响应格式异常，未找到生成内容')

    raw_data = _extract_json(content)
    form_schema = _normalize_schema(raw_data)

    return {
        'form_schema': form_schema,
        'raw': content,
    }


# ---------------------------------------------------------------------------
# AI 流程生成
# ---------------------------------------------------------------------------
FLOW_SYSTEM_PROMPT = """你是一个流程设计专家，服务于 IT 运维自动化工作流平台。根据用户的自然语言描述，生成一个审批流程的 JSON 定义。

平台业务场景参考：
- 服务器申请：用户填写主机名、CPU、内存、操作系统、预算金额等 → 部门主管审批 →（金额>1万则 CFO 审批）→ 运维自动开通 → 通知申请人
- 权限开通：用户填写系统名称、权限类型、理由 → 主管审批 → 运维办理
- 故障报修：用户填写故障描述、影响范围、紧急程度 → IT 经理分配 → 运维处理 → 确认关闭
- 采购审批：用户填写物品、数量、预算 → 部门经理审批 → 采购部审核 → 财务审批

请严格按照用户描述的场景生成对应流程，不要替用户决定流程类型。

要求：
1. 输出必须是严格的 JSON，不要包含任何解释文字、Markdown 代码块标记或注释。
2. JSON 结构必须为工作流引擎兼容格式：
{
  "flow_def": {
    "nodeConfig": {
      "key": "start",
      "name": "发起人",
      "type": 0,
      "childNode": {
        "key": "gateway_1",
        "name": "金额判断",
        "type": 4,
        "conditionNodes": [
          {
            "name": "金额>10万",
            "conditionExpression": "amount > 100000",
            "priorityLevel": 1,
            "childNode": {
              "key": "node_1",
              "name": "总经理审批",
              "type": 1,
              "assigneeType": 3,
              "assigneeIds": [],
              "childNode": {
                "key": "end",
                "name": "结束",
                "type": 9
              }
            }
          },
          {
            "name": "金额<=10万",
            "conditionExpression": "amount <= 100000",
            "priorityLevel": 2,
            "childNode": {
              "key": "node_2",
              "name": "部门经理审批",
              "type": 1,
              "assigneeType": 2,
              "assigneeIds": [],
              "childNode": {
                "key": "end",
                "name": "结束",
                "type": 9
              }
            }
          }
        ]
      }
    },
    "workFlowDef": {
      "id": "wf_generated",
      "icon": "approval",
      "name": "流程名称",
      "cancelable": 1
    },
    "flowPermission": {
      "type": 0,
      "flowInitiators": []
    }
  }
}

节点类型（type）必须使用数字：
- 0: 发起人节点（START，流程起点）
- 1: 审批人节点（APPROVE，需要指定审批人或角色）
- 2: 抄送人节点（COPY，通知相关人员）
- 4: 排他网关节点（EXCLUSIVE_GATEWANY，条件分支，包含 conditionNodes 数组）
- 5: 办理人节点（TRANSACT，执行具体操作）
- 9: 结束节点（END，流程终点）

重要：当需要条件分支时，必须使用 type: 4（排他网关），并在 conditionNodes 数组中定义各个分支条件。

审批人节点属性：
- assigneeType: 审批人类型（数字）
  - 0: 发起人本人（SELF）
  - 1: 上级（SUPERIOR）
  - 2: 部门负责人（DEPARTMENT_LEADER）
  - 3: 角色（ROLE）
  - 4: 指定成员（ASSIGNEE）
- assigneeIds: 审批人/角色 ID 列表（数组）
- approveType: 审批方式（数字）
  - 0: 或签（OR，一人通过即可）
  - 1: 会签（AND，所有人通过）
  - 2: 依次审批（ONE）

条件分支节点属性（type: 4，排他网关）：
- conditionNodes: 条件分支数组，每个分支包含：
  - name: 分支名称（如"金额>10万"）
  - conditionExpression: 条件表达式（字符串）
  - priorityLevel: 优先级（数字，从1开始）
  - childNode: 该分支下的子流程

节点关系：
- childNode: 下一个节点对象
- conditionNodes: 条件分支数组（仅条件节点 type:3 有）

流程名称必须简洁明了，如"请假审批"、"费用报销"等。
请生成结构清晰、类型正确的流程定义。"""


def generate_flow(config: AIConfig, prompt: str, current_form: dict = None) -> dict:
    """调用 AI 生成流程定义

    Args:
        config: AIConfig 实例
        prompt: 用户的自然语言描述
        current_form: 当前表单 schema，用于生成匹配的流程

    Returns:
        {"flow_def": {...}, "raw": "..."}
    """
    api_base = config.effective_api_base()
    api_key = config.effective_api_key()
    model_id = config.effective_model_id()

    if not api_base:
        raise AIServiceError(f'提供商「{config.get_provider_display()}」未配置 API 端点')
    if not api_key:
        raise AIServiceError(
            f'提供商「{config.get_provider_display()}」未配置 API Key，'
            f'请在环境变量中设置 {config.api_key_env_name()}'
        )

    # 构建用户提示
    user_content = f'请为以下需求生成审批流程：\n{prompt}'
    if current_form:
        form_fields = [r.get('title', r.get('field')) for r in current_form.get('rules', [])]
        if form_fields:
            user_content += f'\n\n关联表单包含以下字段：{", ".join(form_fields)}'

    body = {
        'model': model_id,
        'messages': [
            {'role': 'system', 'content': FLOW_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_content},
        ],
        'temperature': 0.3,
        'response_format': {'type': 'json_object'},
    }

    headers = {
        'Content-Type': 'application/json',
    }
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    req = urllib.request.Request(
        api_base,
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method='POST',
    )

    timeout = getattr(settings, 'AI_REQUEST_TIMEOUT', 120)  # 流程生成可能需要更长时间
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='ignore')[:500]
        logger.error('AI 流程生成请求失败: %s %s', e.code, detail)
        raise AIServiceError(f'AI 服务返回错误（{e.code}）: {detail}')
    except urllib.error.URLError as e:
        logger.error('AI 流程生成连接失败: %s', e.reason)
        raise AIServiceError(f'无法连接 AI 服务: {e.reason}')
    except Exception as e:
        logger.error('AI 流程生成请求异常: %s', e)
        raise AIServiceError(f'AI 请求异常: {e}')

    # 解析响应
    try:
        content = payload['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise AIServiceError('AI 响应格式异常，未找到生成内容')

    raw_data = _extract_json(content)
    
    # 确保返回结构正确
    flow_def = raw_data.get('flow_def') or raw_data
    
    return {
        'flow_def': flow_def,
        'raw': content,
    }



# ---------------------------------------------------------------------------
# 流式 AI 生成
# ---------------------------------------------------------------------------

def _build_flow_messages(prompt: str, current_form: dict = None) -> list:
    """构建流程生成的消息列表"""
    user_content = f'请为以下需求生成审批流程：\n{prompt}'
    if current_form:
        form_fields = [r.get('title', r.get('field')) for r in current_form.get('rules', [])]
        if form_fields:
            user_content += f'\n\n关联表单包含以下字段：{", ".join(form_fields)}'
    
    return [
        {'role': 'system', 'content': FLOW_SYSTEM_PROMPT},
        {'role': 'user', 'content': user_content},
    ]


def _build_form_messages(prompt: str) -> list:
    """构建表单生成的消息列表"""
    return [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f'请为以下需求生成表单：\n{prompt}'},
    ]


def _make_stream_request(config: AIConfig, messages: list, timeout: int = 300):
    """发送流式请求到 AI API，返回生成器"""
    api_base = config.effective_api_base()
    api_key = config.effective_api_key()
    model_id = config.effective_model_id()

    if not api_base:
        raise AIServiceError(f'提供商「{config.get_provider_display()}」未配置 API 端点')
    if not api_key:
        raise AIServiceError(
            f'提供商「{config.get_provider_display()}」未配置 API Key，'
            f'请在环境变量中设置 {config.api_key_env_name()}'
        )

    body = {
        'model': model_id,
        'messages': messages,
        'temperature': 0.3,
        'stream': True,
    }

    headers = {
        'Content-Type': 'application/json',
    }
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    req = urllib.request.Request(
        api_base,
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method='POST',
    )

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='ignore')[:500]
        logger.error('AI 流式请求失败: %s %s', e.code, detail)
        raise AIServiceError(f'AI 服务返回错误（{e.code}）: {detail}')
    except urllib.error.URLError as e:
        logger.error('AI 连接失败: %s', e.reason)
        raise AIServiceError(f'无法连接 AI 服务: {e.reason}')
    except Exception as e:
        logger.error('AI 请求异常: %s', e)
        raise AIServiceError(f'AI 请求异常: {e}')


def stream_generate_form(config: AIConfig, prompt: str):
    """流式生成表单
    
    Yields:
        str: SSE 格式的事件数据
    """
    messages = _build_form_messages(prompt)
    
    try:
        resp = _make_stream_request(config, messages, timeout=180)
        
        full_content = ''
        for line in resp:
            if not line:
                continue
            line = line.decode('utf-8').strip()
            if not line.startswith('data: '):
                continue
            data = line[6:]
            if data == '[DONE]':
                break
            try:
                chunk = json.loads(data)
                choices = chunk.get('choices', [])
                if choices and len(choices) > 0:
                    delta = choices[0].get('delta', {})
                    # 流式输出思考过程
                    reasoning = delta.get('reasoning_content') or delta.get('thinking', '')
                    if reasoning:
                        yield json.dumps({'type': 'thinking', 'content': reasoning}) + '\n'
                    content = delta.get('content', '')
                    if content:
                        full_content += content
                        yield json.dumps({'type': 'content', 'content': content}) + '\n'
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.debug('Stream chunk parse error: %s', e)
                continue
        
        # 解析完整内容
        try:
            raw_data = _extract_json(full_content)
            form_schema = _normalize_schema(raw_data)
            yield json.dumps({'type': 'result', 'form_schema': form_schema}) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f'解析失败: {str(e)}'}) + '\n'
            
    except AIServiceError as e:
        yield json.dumps({'type': 'error', 'message': str(e)}) + '\n'
    except Exception as e:
        yield json.dumps({'type': 'error', 'message': f'生成失败: {str(e)}'}) + '\n'


def stream_generate_flow(config: AIConfig, prompt: str, current_form: dict = None):
    """流式生成流程
    
    Yields:
        str: SSE 格式的事件数据
    """
    messages = _build_flow_messages(prompt, current_form)
    
    try:
        resp = _make_stream_request(config, messages, timeout=300)
        
        full_content = ''
        for line in resp:
            if not line:
                continue
            line = line.decode('utf-8').strip()
            if not line.startswith('data: '):
                continue
            data = line[6:]
            if data == '[DONE]':
                break
            try:
                chunk = json.loads(data)
                choices = chunk.get('choices', [])
                if choices and len(choices) > 0:
                    delta = choices[0].get('delta', {})
                    # 流式输出思考过程（reasoning_content / thinking）
                    reasoning = delta.get('reasoning_content') or delta.get('thinking', '')
                    if reasoning:
                        yield json.dumps({'type': 'thinking', 'content': reasoning}) + '\n'
                    content = delta.get('content', '')
                    if content:
                        full_content += content
                        yield json.dumps({'type': 'content', 'content': content}) + '\n'
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.debug('Stream chunk parse error: %s', e)
                continue
        
        # 解析完整内容
        try:
            raw_data = _extract_json(full_content)
            flow_def = raw_data.get('flow_def') or raw_data
            yield json.dumps({'type': 'result', 'flow_def': flow_def}) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f'解析失败: {str(e)}'}) + '\n'
            
    except AIServiceError as e:
        yield json.dumps({'type': 'error', 'message': str(e)}) + '\n'
    except Exception as e:
        yield json.dumps({'type': 'error', 'message': f'生成失败: {str(e)}'}) + '\n'
