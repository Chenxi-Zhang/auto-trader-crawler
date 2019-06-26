# auto-trader-crawler

----
### 目的

* 爬取[auto trader](https://www.autotrader.ca)上的二手车信息，用作其他项目的数据集。   

----
### 前期调研
* 寻找url规律。通过观察，发现：
* 所有公开的二手车辆信息在子目录`/icon/${make}/${model}/[${province/city} || ${city/province}]/${carUID}`。   
* 车辆的信息在车辆页面`id=vdp-specs-content`的tag里，以`<table>`tag储存。 
* 二手车信息的list在子目录`/cars/${make}`。   
* 所有车辆`${make}`(品牌)在主页的`<optgroup label="All Makes">`tag里。   
* 爬取的思路很清晰：   
* 先把品牌储存起来。    
* 选定一个品牌，将`/cars/${make}`的所有子页面爬完。将数据以某种序列化方式储存起来。

---
### 开发经验
* 底层简单封装，把需要用的库，类，以及方法进行简单的改写和组合。需要的方法包括：url的拼接、改写，对某url进行request访问，将response美化解析（BeautifulSoup4），对某个soup对象进行遍历某pattern的tag（比如`<a>`）的操作，数据序列化和反序列化。随着开发进行，更多的方法加入。
* 高层api设计：
* 读取品牌的类。可以读取品牌名字与该品牌item的个数，返回dict。可以将该dict写入文件，并本地读取。如果传入threshold参数，会从网页爬取所有品牌item个数高于阈值的品牌。默认阈值为1000。
* ~~读取车辆信息的类。必须传入url。可以request，可以解析response，可以判断是否是包含车辆信息的网页，如果是，同时将信息保存为dict。~~
* 由于需要大量请求，采用异步方式进行request，故不再包装url或者response，仅仅提供解析。
* 爬取所有车辆的类。必须传入品牌名字（str），品牌商品数目（int）。通过设置偏移来显示所有车辆连接。比如`/cars/${make}?rcp=${record per page}&rcs=${offset}`，rcp代表每页显示车辆个数，对应数据库的`limit`，rcs代表其在数据库上的偏移`offset`。
* 多线程提高单机爬取效率。
* 异步非阻塞网络编程。高效爬虫程序更多依靠异步非阻塞的方式进行request。
* 没有进行https访问设计，某些页面无法爬取。

----
### 性能瓶颈
* 在异步request的条件下，分析页面的速度成为瓶颈，cpu计算性能的提升将会提高爬取速度。可以考虑分布式爬取。

---
### 分布式扩展
* 消息中间件。RabbitMQ
