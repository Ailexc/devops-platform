"""关系变更执行器：图谱编辑 -> 关系变更工单 -> 审批通过 -> 落库 ResourceRelation"""
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def apply_relation_changes(ticket):
    """执行关系变更（新增/删除/变更依赖强度），全部成功才置成功"""
    from .models import Resource, ResourceChange, ResourceRelation

    changes = (ticket.request_content or {}).get('changes') or []
    results = []
    all_ok = True

    for ch in changes:
        action = ch.get('action')
        source_id = ch.get('source_id')
        target_id = ch.get('target_id')
        relation_type = ch.get('relation_type', 'depends_on')
        strength = ch.get('strength', 'hard')
        result = {'action': action, 'source_id': source_id, 'target_id': target_id,
                  'relation_type': relation_type, 'strength': strength}
        try:
            if action == 'add':
                rel, created = ResourceRelation.objects.get_or_create(
                    source_id=source_id, target_id=target_id, relation_type=relation_type,
                    defaults={'strength': strength, 'relation_source': 'manual'},
                )
                result['ok'] = True
                result['message'] = f'已建立 {relation_type}({strength})' if created else '依赖已存在'
            elif action == 'remove':
                deleted, _ = ResourceRelation.objects.filter(
                    source_id=source_id, target_id=target_id, relation_type=relation_type
                ).delete()
                result['ok'] = bool(deleted)
                result['message'] = '已移除依赖' if deleted else '依赖不存在'
            elif action == 'update':
                updated = ResourceRelation.objects.filter(
                    source_id=source_id, target_id=target_id, relation_type=relation_type
                ).update(strength=strength)
                result['ok'] = bool(updated)
                result['message'] = f'依赖强度已更新为 {strength}'
            else:
                result['ok'] = False
                result['message'] = '未知操作'
                all_ok = False
        except Exception as e:  # noqa: BLE001
            logger.exception('关系变更执行失败')
            result['ok'] = False
            result['message'] = str(e)[:150]
            all_ok = False

        results.append(result)
        if result['ok'] and source_id:
            try:
                src = Resource.objects.get(id=source_id)
                ResourceChange.objects.create(
                    resource=src, action=f'relation_{action}', after_data=ch,
                    operator=ticket.applicant, source='ticket', ticket_id=ticket.ticket_no,
                )
            except Resource.DoesNotExist:
                pass

    ticket.result_content = {'changes': results}
    ticket.status = 'success' if all_ok else 'failed'
    if not all_ok:
        ticket.fail_reason = '存在失败的关系变更，请检查工单详情'
    ticket.finished_at = timezone.now()
    ticket.save()
