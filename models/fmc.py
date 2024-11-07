class CdFmcAccessPolicy:
    def __init__(self, name: str, default_action: str = "BLOCK"):
        self.type = "AccessPolicy"
        self.name = name
        self.defaultAction = {"action": default_action}


class UrlCategory:
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        self.type = "URLCategory"

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "type": self.type,
        }


class UrlCategoryWithReputation:
    def __init__(self, reputation: str, category: UrlCategory):
        self.reputation = reputation
        self.category = category
        self.type = "UrlCategoryAndReputation"

    def to_dict(self):
        return {
            "reputation": self.reputation,
            "category": self.category.to_dict(),
            "type": self.type,
        }


class Urls:
    def __init__(self, url_categories_with_reputation: list[UrlCategoryWithReputation]):
        self.urlCategoriesWithReputation = url_categories_with_reputation

    def to_dict(self):
        return {
            "urlCategoriesWithReputation": [
                ucr.to_dict() for ucr in self.urlCategoriesWithReputation
            ],
        }


class NetworkObject:
    def __init__(self, type: str, overridable: bool, id: str, name: str):
        self.type = type
        self.overridable = overridable
        self.id = id
        self.name = name

    def to_dict(self):
        return {
            "type": self.type,
            "overridable": self.overridable,
            "id": self.id,
            "name": self.name,
        }


class SourceNetworks:
    def __init__(self, objects: list[NetworkObject]):
        self.objects = objects

    def to_dict(self):
        return {
            "objects": [obj.to_dict() for obj in self.objects],
        }


class CdFmcAccessRule:
    def __init__(
        self,
        name: str,
        action: str,
        enabled: bool,
        urls: Urls,
        source_networks: SourceNetworks,
    ):
        self.name = name
        self.action = action
        self.enabled = enabled
        self.urls = urls
        self.source_networks = source_networks

    def to_dict(self):
        return {
            "name": self.name,
            "action": self.action,
            "enabled": self.enabled,
            "urls": self.urls.to_dict(),
            "sourceNetworks": self.source_networks.to_dict(),
        }
