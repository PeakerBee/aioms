from enum import Enum


class RouteType(Enum):
    HTTP = 1
    REDIS_RPC = 2


class RouteDefinition:
    def __init__(self, route_id: str, uri: str, route_type: 'RouteType' = RouteType.HTTP, throttling=False):
        self.route_id = route_id
        self.uri = uri
        self.route_type = route_type
        self.throttling = throttling


class Route:
    def __init__(self, route_id: str, uri: str, route_type: 'RouteType' = RouteType.HTTP, throttling=False):
        self.route_id = route_id
        self.uri = uri
        self.route_type = route_type
        self.throttling = throttling
