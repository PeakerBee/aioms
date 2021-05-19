from typing import List

from gateway.route.definition import RouteDefinition, Route


class RouteLocator:

    def get_routes(self) -> List['Route']:
        raise NotImplementedError()

    def convert_to_route(self, route_instance: 'RouteDefinition'):
        raise NotImplementedError()


class RouteDefinitionLocator:

    def get_route_definitions(self) -> List[RouteDefinition]:
        raise NotImplementedError()


class RouteDefinitionRouteLocator(RouteLocator):

    def __init__(self, route_def_locator: 'RouteDefinitionLocator'):
        self.route_definition_locator = route_def_locator

    def get_routes(self) -> List['Route']:
        return list(map(self.convert_to_route, self.route_definition_locator.get_route_definitions()))

    def convert_to_route(self, route_instance: 'RouteDefinition') -> Route:
        return Route(route_id=route_instance.route_id, uri=route_instance.uri, route_type=route_instance.route_type)
