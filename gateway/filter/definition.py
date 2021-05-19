from gateway.web.http import ServerWebExchange


class GatewayFilter:
    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        raise NotImplementedError()


class GatewayFilterChain:
    def filter(self, exchange: 'ServerWebExchange'):
        raise NotImplementedError()
