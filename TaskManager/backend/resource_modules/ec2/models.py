"""
EC2 CMDB models — virtual ORM models for EC2-related resource types.

Uses CmdbQuerySet as the storage backend.  In development this works
with an in-memory store; in production it connects to the real CMDB service.
"""

from core.cmdb_queryset import CmdbQuerySet


class CmdbEC2:
    """Virtual model for EC2 instances in CMDB."""
    objects = CmdbQuerySet("EC2")

    class DoesNotExist(CmdbQuerySet.model.DoesNotExist):
        pass

    class MultipleObjectsReturned(CmdbQuerySet.model.MultipleObjectsReturned):
        pass


class CmdbSecurityGroup:
    """Virtual model for Security Groups in CMDB."""
    objects = CmdbQuerySet("SecurityGroup")

    class DoesNotExist(CmdbQuerySet.model.DoesNotExist):
        pass

    class MultipleObjectsReturned(CmdbQuerySet.model.MultipleObjectsReturned):
        pass


class CmdbNetworkInterface:
    """Virtual model for Network Interfaces in CMDB."""
    objects = CmdbQuerySet("NetworkInterface")

    class DoesNotExist(CmdbQuerySet.model.DoesNotExist):
        pass

    class MultipleObjectsReturned(CmdbQuerySet.model.MultipleObjectsReturned):
        pass
