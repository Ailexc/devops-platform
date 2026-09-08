import os
from django.db import models


class TimeStampedModel(models.Model):
    """抽象基类，提供创建/更新时间字段。"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True


class AIConfig(TimeStampedModel):
    """AI 配置（用于 AI 表单生成等能力）"""

    class Provider(models.TextChoices):
        XIAOMI = 'xiaomi', '小米 MiMo'
        OPENAI = 'openai', 'OpenAI'
        DEEPSEEK = 'deepseek', 'DeepSeek'
        ZHIPU = 'zhipu', '智谱 GLM'
        QWEN = 'qwen', '通义千问'
        OLLAMA = 'ollama', '本地 Ollama'

    # 提供商默认模型与端点（可在创建时覆盖）
    PROVIDER_DEFAULTS = {
        Provider.XIAOMI: {
            'model_id': 'mimo-v2.5',
            'api_base': 'https://api.xiaomimimo.com/v1/chat/completions',
        },
        Provider.OPENAI: {
            'model_id': 'gpt-4o',
            'api_base': 'https://api.openai.com/v1/chat/completions',
        },
        Provider.DEEPSEEK: {
            'model_id': 'deepseek-chat',
            'api_base': 'https://api.deepseek.com/v1/chat/completions',
        },
        Provider.ZHIPU: {
            'model_id': 'glm-4',
            'api_base': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        },
        Provider.QWEN: {
            'model_id': 'qwen-max',
            'api_base': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        },
        Provider.OLLAMA: {
            'model_id': 'qwen2.5:7b',
            'api_base': 'http://host.docker.internal:11434/v1/chat/completions',
        },
    }

    provider = models.CharField('提供商', max_length=50, choices=Provider.choices)
    model_id = models.CharField('模型 ID', max_length=100, default='', blank=True,
                                help_text='留空则使用提供商默认模型')
    api_base = models.URLField('API 端点', max_length=300, default='', blank=True,
                               help_text='留空则使用提供商默认端点')
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        ordering = ['-is_active', 'provider']
        verbose_name = 'AI 配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.get_provider_display()} ({self.model_id or self.provider})'

    def effective_api_base(self):
        """
        返回实际 API 端点（优先配置，其次环境变量，最后默认值），
        并规范为完整的 chat/completions 地址（兼容只填 /v1 前缀的写法）。
        """
        if self.api_base:
            base = self.api_base
        else:
            env_key = f"AI_{self.provider.upper()}_API_BASE"
            base = os.environ.get(env_key, '') or self.PROVIDER_DEFAULTS.get(self.provider, {}).get('api_base', '')
        return self._normalize_api_base(base)

    def effective_api_key(self):
        """返回实际 API Key（仅从环境变量读取，不落库）"""
        return os.environ.get(self.api_key_env_name(), '')

    def api_key_env_name(self):
        """该提供商对应的 API Key 环境变量名，如 AI_XIAOMI_API_KEY"""
        return f"AI_{self.provider.upper()}_API_KEY"

    def has_api_key(self):
        """环境变量中是否配置了 API Key"""
        return bool(self.effective_api_key())

    @staticmethod
    def _normalize_api_base(base: str) -> str:
        """将 /v1 之类的前缀规范为完整的 chat/completions 地址"""
        base = (base or '').strip().rstrip('/')
        if not base:
            return ''
        if base.endswith('/chat/completions'):
            return base
        return base + '/chat/completions'

    def effective_model_id(self):
        """返回实际模型 ID（优先配置，其次默认）"""
        if self.model_id:
            return self.model_id
        return self.PROVIDER_DEFAULTS.get(self.provider, {}).get('model_id', '')

    @classmethod
    def get_default(cls):
        """获取默认启用的 AI 配置（provider=xiaomi 优先，其次任意 is_active）"""
        config = cls.objects.filter(is_active=True).first()
        if config:
            return config
        return cls(provider=cls.Provider.XIAOMI)
