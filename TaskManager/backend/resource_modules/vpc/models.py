"""
VPC CMDB models.
"""

from core.cmdb_queryset import CmdbQuerySet


class CmdbVPC:
    objects = CmdbQuerySet("VPC")

    class DoesNotExist(CmdbQuerySet.model.DoesNotExist):
        pass

    class MultipleObjectsReturned(CmdbQuerySet.model.MultipleObjectsReturned):
        pass


class CmdbSubnet:
    objects = CmdbQuerySet("Subnet")

    class DoesNotExist(CmdbQuerySet.model.DoesNotExist):
        pass

    class MultipleObjectsReturned(CmdbQuerySet.model.MultipleObjectsReturned):
        pass
