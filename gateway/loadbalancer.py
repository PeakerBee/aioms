import random
from typing import List, Any


class LoadBalancerRule:

    def choose(self, services: List['Any']) -> Any:
        pass


class RandomRule(LoadBalancerRule):

    def choose(self, services: List['Any']) -> Any:
        if len(services) > 0:
            index = random.randint(0, len(services) - 1)
            return services[index]
