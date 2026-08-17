"""
RDS CMDB models.
"""

from core.cmdb_queryset import CmdbQuerySet


class CmdbRDS:
    objects = CmdbQuerySet("RDS")

    class DoesNotExist(CmdbQuerySet.model.DoesNotExist):
        pass

    class MultipleObjectsReturned(CmdbQuerySet.model.MultipleObjectsReturned):
        pass
