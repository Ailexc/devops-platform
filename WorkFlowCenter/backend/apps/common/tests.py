import os

from django.test import TestCase

from .models import AIConfig
from .services.ai_service import AIServiceError, generate_form


class AIConfigKeyTest(TestCase):
    """API Key 环境变量配置与端点规范化"""

    def test_api_key_read_from_env(self):
        os.environ['AI_XIAOMI_API_KEY'] = 'env-secret'
        try:
            cfg = AIConfig(provider='xiaomi')
            self.assertEqual(cfg.effective_api_key(), 'env-secret')
            self.assertTrue(cfg.has_api_key())
            self.assertEqual(cfg.api_key_env_name(), 'AI_XIAOMI_API_KEY')
        finally:
            os.environ.pop('AI_XIAOMI_API_KEY', None)

    def test_api_key_not_stored_on_model(self):
        cfg = AIConfig(provider='openai')
        self.assertFalse(hasattr(cfg, 'api_key'))

    def test_api_base_normalization(self):
        cfg = AIConfig(provider='openai')
        self.assertEqual(
            cfg._normalize_api_base('https://api.openai.com/v1'),
            'https://api.openai.com/v1/chat/completions',
        )
        self.assertEqual(
            cfg._normalize_api_base('https://api.openai.com/v1/chat/completions/'),
            'https://api.openai.com/v1/chat/completions',
        )
        self.assertEqual(cfg._normalize_api_base(''), '')

    def test_missing_key_raises_clear_error(self):
        os.environ.pop('AI_XIAOMI_API_KEY', None)
        cfg = AIConfig(provider='xiaomi')
        with self.assertRaises(AIServiceError) as ctx:
            generate_form(cfg, '生成一个反馈意见表单')
        self.assertIn('AI_XIAOMI_API_KEY', str(ctx.exception))
