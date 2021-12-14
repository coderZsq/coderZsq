iOS 深圳

1. 两个整数相加;
2. Runloop 的 mode？ autorelease 的释放时机?
3. runtime 的 category 中实现了跟他一样的一个方法会怎么样？
4. kvo 的实现，有没有遇到过崩溃
5. 单例的优缺点 -
6. sqlite 什么时候适合用索引

7. 算法, atoi -
8. autoreleasepool 实现原理
9. 自旋锁, 互斥锁
10. Swift, OC 差异 -
11. HTTPS 加密与身份验证
12. TCP, UDP 区别 -
13. TCP 拥塞控制原理
14. SDWebImage -
15. 图片解码 -
16. 指针混淆 -
17. TagPointer

1、NSString 为什么用 copy 修饰 -
2、重写 isEqual 方法，hash 方法的作用，引出 NSSet 的读写效率比较高 -
3、performselector 和直接调用方法哪个执行快
4、为什么一个线程只能有一个 runloop
5、子线程的 runloop 开启后，如果不做任何操作，线程会被杀死吗？ -
6、load 方法是在什么时候调用的
7、initialize 方法是干嘛用的？是什么时候调用的 -
8、repeated 的 NSTimer 有什么性能问题

1. 算法：二叉树的左右子树交换代码实现； -
2. 页面路由如何实现，如何去维护一张路由表；页面是如何去进行跳转的（runtime）；路由表中的键和值分别是什么？如何根据服务器下发的数据加载页面； -
3. js 和 OC 如何调用；（js 是怎样调用 oc 的）；-
4. GCD 和 NSOperation 的区别；哪一个的复用性更好；NSOperation 的队列可以 cancel 吗，里面的任务可以 cancel 吗；
5. block 和 self 的循环引用；到底是如何循环引用的；-
6. SDWebImage 的缓存策略，是如何从缓存中 hit 一张图片的；使用了几级缓存；缓存如何满了如何处理，是否要设置过期时间； -
7. 讲讲 RunLoop -
8. 讲讲 iOS 动画，比如 CoreAnimation； -
9. 屏幕上点击一个 View，事件是如何去响应的； -
10. 深拷贝与浅拷贝；-

11. 属性有哪些修饰符 -
12. 将一个 NSArray 赋值给一个 copy 修饰的 NSMutableArray 属性，然后尝试向这个可变数组添加对象，会发生什么？ -
13. Category 同名方法 -
14. Extention 可以有多个吗？
15. Category 多个同名方法怎么进行 Method swizzing -
16. GCD 串行队列和并行队列执行顺序分析 -
17. NSOperator 执行顺序分析，maxConcurrent 为 2 或者 1 两种情况 -
18. 100 亿个数求 top k，算法复杂度，怎么在算法最优的情况下再快 100 倍？-
19. KVO 的实现原理，一个类的多次 kvo 会生成多个新类吗？是直接就对所有的属性都生成 kvo 的方法吗？-
20. http 返回码有哪些，206 返回码，断点续传
21. https 握手原理，能确保安全吗 -
22. runloop 原理，几种 mode -
23. autoreleasepool 原理？如果对一个对象写了多次 autorelease，会怎样？ -
24. weak table 是用的什么数据结构
25. block 几种内存类型，如何捕获变量
26. 注意 copy 和 mutableCopy 方法，有陷阱，
27. @synchronized(xxx)的实现
28. atomic 实现原理。

29. 实现 Power()函数
30. TCP 的断包粘包如何避免
