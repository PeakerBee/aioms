# AsyncIO Micro Service Framework
基于tornado的一个微服务基础框架 
## Introduce

使用python做web开发面临的一个最大的问题就是性能，在解决C10K问题上显的有点吃力。有些异步框架Tornado、Twisted、Gevent 等就是为了解决性能问题。这些框架在性能上有些提升，且异步框架并发性只是在IO密集型业务有优势，对于CPU密集业务优势也并不是很明显，同时由于是使用异步函数和我们平时同步开发逻辑有些许不同，说以会出现各种古怪的问题难以解决。

在python3.6中，官方的异步协程库asyncio正式成为标准。在保留便捷性的同时对性能有了很大的提升, 已经出现许多的异步框架使用asyncio， 如Tornado。本项目就是以Tornado为基础搭建的微服务框架。微服务最近很火，它解决了复杂性和并发性问题，提高开发效率，便于部署等优点，同时由于Tornado在异步上的优势。我们就以Tornado为基础，集成多个流行的库搭建微服务框架。

## Feature

* **使用tornado异步框架，简单，轻量，高效。**
* **使用asyncio为核心引擎，使tornado在很多情况下单机单进程并发甚至不亚于Golang，Java。**
* **1.0版本，微服务之间的RPC是基于redis创建的消息总线，利用消息总线进行RPC**
* **2.0版本，使用AsyncHTTPClient作为http client，使用http协议进行微服务之间的RPC。**
* **参考Java Spring Cloud，也开发了限流，熔断等功能，利用责任链模式动态接入网关中提高系统稳定性**
* **使用Zookeeper作为协调服务器，进行服务动态注册发现和下线**
* **使用skywalking为分布式追踪系统。记录微服务之间的调用链**
* **使用unittest做单元测试，并且使用mock来避免访问其他微服务。**
* **使用pydoc自动生成API文档。由于Tornado对Swagger API支持的并不是很好，后续会研究看看有什么解决方案将Swagger API接入，这样就可以把接口文档同步到接口平台上**

## Usage
python3.7+ 环境 使用tornado为基础框架进行扩展

### 安装依赖包

python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

python -m pip install -r reqs.txt -i https://mirrors.aliyun.com/pypi/simple

python -m pip freeze > reqs.txt  