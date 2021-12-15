## iOS Interview

1. 两个整数相加;

```cpp
int getSum(int a, int b){
    while (b != 0) {
        int carry = (unsigned int)(a & b) << 1;
        a = a ^ b;
        b = carry;
    }
    return a;
}
```

```
思路:
- a + b的问题拆分为 (a + b 无进位的结果) 和 (a 和 b的进位结果)
- 无进位加法使用异或运算计算得出
- 进位结果使用与运算和移位运算计算得出
- 循环此过程, 直到进位为0
```

2. Runloop 的 mode？ autorelease 的释放时机?

```
Runloop 的 mode

- Runloop: RunLoop启动时只能选择其中一个Mode，作为currentMode
  - mode (currentMode) kCFRunLoopDefaultMode: App的默认Mode, 通常主线程是在这个Mode下运行
    - timers NSTimer / performSelector:withObject:afterDelay:
    - source0 触摸事件处理 / performSelector:onThread
    - source1 基于Port的线程间通信 / 系统事件捕捉
    - observers 用于监听RunLoop的状态
      - kCFRunLoopEntry          // 即将进入Loop
      - kCFRunLoopBeforeTimers   // 即将处理Timer
      - kCFRunLoopBeforeSources  // 即将处理Source
      - kCFRunLoopBeforeWaiting  // 即将进入休眠 + UI刷新 + Autorealease pool // 等待 mach_port消息
      - kCFRunLoopAfterWaiting   // 刚从休眠中唤醒 // 接收 mach_port消息
      - kCFRunLoopExit           // 即将退出Loop
      - kCFRunLoopAllActivities
  - mode UITrackingRunLoopMode: 界面跟踪 Mode，用于 ScrollView 追踪触摸滑动，保证界面滑动时不受其他 Mode 影响
    - timers
    - source0
    - source1
    - observers

- 如果需要切换Mode，只能退出当前Loop，再重新选择一个Mode进入
- 不同组的Source0/Source1/Timer/Observer能分隔开来，互不影响
- 如果Mode里没有任何Source0/Source1/Timer/Observer，RunLoop会立马退出

```

```
autorelease 的释放时机

答案: 当 RunLoop 处于 kCFRunLoopBeforeWaiting, kCFRunLoopBeforeExit时释放

iOS在主线程的Runloop中注册了2个Observer
- 第1个Observer监听了kCFRunLoopEntry事件，会调用objc_autoreleasePoolPush()
- 第2个Observer
  - 监听了kCFRunLoopBeforeWaiting事件，会调用objc_autoreleasePoolPop()、objc_autoreleasePoolPush()
  - 监听了kCFRunLoopBeforeExit事件，会调用objc_autoreleasePoolPop()

```

3. runtime 的 category 中实现了跟他一样的一个方法会怎么样？

```
答案: 会直接被category中的方法覆盖
```

```
Category 实现原理

- Category编译之后的底层结构是struct category_t，里面存储着分类的对象方法、类方法、属性、协议信息
- 在程序运行的时候，runtime会将Category的数据，合并到类信息中(类对象、元类对象中)
*rw = category(属性 协议 方法) -> +  ro
*分类结构中没有成员变量

category_t
  - name               // 分类名
  - cls                // 宿主类
  - instanceMethods    // 实例方法
  - classMethods       // 类方法
  - protocols          // 协议
  - instanceProperties // 实例属性
  - classProperties    // 类属性

Category 加载处理过程 (运行时决议)
1. 通过 Runtime 加载某个类色所有 Category 数据
2. 把所有 Category 的方法,属性,协议数据合并到一个大数组中, 后面参与编译的Category,会在数组的前面
3. 将合并后的分类数据 (方法,属性,协议), 插入到类原来数据的前面

Category和Class Extension的区别是什么?
- Class Extension在编译的时候，它的数据就已经包含在类信息中
- Category是在运行时，才会将数据合并到类信息中
*类扩展其实是类的一部分, 编译期决议, 分类是运行时决议
```

```
Category能否添加成员变量?如果可以，如何给Category添加成员变量?
- 不能直接给Category添加成员变量，但是可以间接实现Category有成员变量的效果
*原因是分类数据结构没有定义字段, 可以使用关联对象绑定
```

```
关联对象

AssociationsManager {             // 单例对象
  map AssociationsHashMap {       // 持有一个哈希表
    obj : disguised_ptr_t         // 存放每个对象
    map : ObjectAssociationMap {  // 存放每个对象拥有的成员变量哈希表
        key : void * // 唯一性key
        value : ObjcAssociation { // 成员变量值包装类
          policy : uintptr_t  // 内存策略
          id     : value      // 实际变量值
        }
    }
  }
}
```

4. kvo 的实现，有没有遇到过崩溃

```
kvo 的实现

答案: 用Runtime动态生成一个子类,并让instance对象isa指向这个全新的子类
*类似Java动态代理CGLib的设计思路, 是一种Proxy模式

有没有遇到过崩溃

1. observe忘记写监听回调方法 observeValueForKeyPath
2. add和remove次数不匹配
3. 监听者和被监听者dealloc之前没有remove（其实也原因2，但是监听者和被监听者的生命周期不同）

情型一、obsever没有实现observeValueForKeyPath方法
情型二、没有移除KVO 比如observer是VC在pop的时候没有在dealloc中removeKVO
情型三、多次移除KVO
情型四、多次添加相同KVO但是remove次数不同（如果add 和remove相匹配不会崩溃 例子中在dealloc中remove两次）
情形五 监听者和被监听者的生命周期不同

解决方案 FBKVOController
```

```
iOS用什么方式实现对一个对象的KVO?(KVO的本质是什么?)
- 利用RuntimeAPI动态生成一个子类，并且让instance对象的isa指向这个全新的子类
- 当修改instance对象的属性时，会调用Foundation的_NSSetXXXValueAndNotify函数
1. willChangeValueForKey
2. 父类原来的setter
3. didChangeValueForKey:
- 内部会触发监听器(Oberser)的监听方法( observeValueForKeyPath:ofObject:change:context:)

如何手动触发KVO?
- 手动调用willChangeValueForKey:和didChangeValueForKey:

直接修改成员变量会触发KVO么?
- 不会触发KVO
*调用了原来的父类的setter方法
```

5. 单例的优缺点

```
答案:
优点:
1. 只有确定整个App中语义唯一性, 可以避免新的内存分配
2. 减少内存开支
3. 减少系统的性能开销
4. 避免对资源的多重占用
缺点:
1. 可测试性差, 应该避免使用
2. 扩展很困难
3. 不适用于变化的对象
4. 例类的职责过重
```

6. sqlite 什么时候适合用索引

```
1. 在经常需要搜索的列上，这是毋庸置疑的
2. 经常同时对多列进行查询，且每列都含有重复值可以建立组合索引，组合索引尽量要使常用查询形成索引覆盖（查询中包含的所需字段皆包含于一个索引中，我们只需要搜索索引页即可完成查询）。
3. 在经常用在连接的列上，这些列主要是一些外键，可以加快连接的速度，连接条件要充分考虑带有索引的表。
4. 在经常需要对范围进行搜索的列上创建索引，因为索引已经排序，其指定的范围是连续的，同样，在经常需要排序的列上最好也创建索引。
5. 在经常放到where子句中的列上面创建索引，加快条件的判断速度。
```

7. 算法, atoi

```cpp
int myAtoi(char * s){
    unsigned long len = strlen(s);
    // 去除前导空格
    int index = 0;
    while (index < len) {
        if (s[index] != ' ') {
            break;
        }
        index++;
    }
    if (index == len) {
        return 0;
    }
    int sign = 1;
    // 处理第 1 个非空字符为正负符号，这两个判断需要写在一起
    if (s[index] == '+') {
        index++;
    } else if (s[index] == '-') {
        sign = -1;
        index++;
    }
    // 根据题目限制，只能使用 int 类型
    int res = 0;
    while (index < len) {
        char curChar = s[index];
        if (curChar < '0' || curChar > '9') { // 如果不是数字, 则直接判定转换失败
            break;
        }
        int num = (curChar - '0'); // 减去ascii表, 获取number
        if (res > INT_MAX / 10 || (res == INT_MAX / 10 && num > INT_MAX % 10)) {
            return INT_MAX;
        }
        if (res < INT_MIN / 10 || (res == INT_MIN / 10 && num > -(INT_MIN % 10))) {
            return INT_MIN;
        }
        res = res * 10 + sign * num;
        index++;
    }
    return res;

}
```

```
字符串的转换
- 明确转化规则
  - 空格处理
  - 正负号处理
  - 数字处理
- [推入]数字
  - result = result * 10 + num
- 模式识别: 整数运算注意溢出
  - 转换为INT_MAX的逆运算
```

8. autoreleasepool 实现原理

```
// 自动释放池的主要底层数据结构是:__AtAutoreleasePool、AutoreleasePoolPage
// 调用了autorelease的对象最终都是通过AutoreleasePoolPage对象来管理的
__AtAutoreleasePool {
  currentPage: AutoreleasePoolPage { // 每个AutoreleasePoolPage对象占用4096字节内存 4kb
    magic: magic_t
    *next: id // 指向了下一个能存放autorelease对象地址的区域
    thread: pthread_t
    parent: AutoreleasePoolPage // 双向链表
    child: AutoreleasePoolPage  // 双向链表
    depth: uint32_t
    hiwat: uint32_t
    ... 剩下的空间用来存放 autorelease 对象的地址
  }
}
- 每个AutoreleasePoolPage对象占用4096字节内存，除了用来存放它内部的成员变量，剩下的空间用来存放 autorelease对象的地址
- 所有的AutoreleasePoolPage对象通过双向链表的形式连接在一起
```

```
autoreleasepool 行为逻辑

- 调用push方法会将一个POOL_BOUNDARY入栈，并且返回其存放的内存地址
- 调用pop方法时传入一个POOL_BOUNDARY的内存地址，会从最后一个入栈的对象开始发送release消息，直到遇到这个
   POOL_BOUNDARY
*双向链表的结构 + 栈的内存管理模式
```

9. 自旋锁, 互斥锁

```
答案

自旋锁: 等待锁的线程会处于忙等状态, 一直占用CPU资源, 不进行线程切换
互斥锁: 等待锁的线程会处于休眠状态, 进行线程切换
*关注点: 操作系统的线程调度算法

什么情况使用自旋锁比较划算?
1. 预计线程等待锁的时间很短
2. 加锁的代码(临界区)经常被调用，但竞争情况很少发生
3. CPU资源不紧张
4. 多核处理器

什么情况使用互斥锁比较划算?
1. 预计线程等待锁的时间较长
2. 单核处理器
3. 临界区有IO操作
4. 临界区代码复杂或者循环量大
5. 临界区竞争非常激烈

*关注点, 加锁临界区的等待操作系统响应时间短的 使用自旋锁, 时间长的用互斥锁,
```

```
线程同步方案:

自旋锁:
- OSSpinLock ”自旋锁”，等待锁的线程会处于忙等(busy-wait)状态，一直占用着CPU资源 (目前已经不再安全，可能会出现优先级反转问题)
如果等待锁的线程优先级较高，它会一直占用着CPU资源，优先级低的线程就无法释放锁

互斥锁:
- os_unfair_lock 从iOS10开始才支持
从底层调用看，等待os_unfair_lock锁的线程会处于休眠状态，并非忙等

- pthread_mutex
”互斥锁”，等待锁的线程会处于休眠状态

- NSLock // 对mutex普通锁的封装
- NSRecursiveLock // 也是对mutex递归锁的封装，API跟NSLock基本一致
- NSCondition // 是对mutex和cond的封装
- NSConditionLock // 是对NSCondition的进一步封装，可以设置具体的条件值

信号量: IPC进程间通信
- dispatch_semaphore
信号量的初始值，可以用来控制线程并发访问的最大数量
信号量的初始值为1，代表同时只允许1条线程访问资源，保证线程同步

串行队列:
- dispatch_queue(DISPATCH_QUEUE_SERIAL)
直接使用GCD的串行队列，也是可以实现线程同步的
```

```
线程同步方案性能比较:
1. os_unfair_lock
2. OSSpinLock
3. dispatch_semaphore
4. pthread_mutex
5. dispatch_queue(DISPATCH_QUEUE_SERIAL)
6. NSLock
7. NSCondition
8. pthread_mutex(recursive)
9. NSRecursiveLock
10. NSConditionLock
11. @synchronized
```

```
读写安全方案:

同一时间，只能有1个线程进行写的操作
同一时间，允许有多个线程进行读的操作
同一时间，不允许既有写的操作，又有读的操作

上面的场景就是典型的“多读单写”，经常用于文件等数据的读写操作，iOS中的实现方案有

1. pthread_rwlock:读写锁 // 等待锁的线程会进入休眠
2. dispatch_barrier_async:异步栅栏调用

- 这个函数传入的并发队列必须是自己通过dispatch_queue_cretate创建的
- 如果传入的是一个串行或是一个全局的并发队列，那这个函数便等同于dispatch_async函数的效果
```

10. Swift, OC 差异

```
编程范式:

OC 结构化 + 面向对象
Swift 结构化 + 面向对象 + 函数式 + 面向协议
*最主要的差异是编程范式进化到了函数式(一等公民, 不可变类型, 值对象, Optional, map, filter, reduce等, SwiftUI声明式)
*主要的转变在于从 怎么做 -> 做什么, 但带来的是新语法太多, 掌握起来困难, 这点不如Go

Swift 类型安全   // 需要明确值的类型
Swift 值类型增强 // 基本都是值类型 和 Go 相同
Swift 枚举增强  // 可以使用各种类型和模式匹配
Swift 泛型编程  // OC的泛型约束只停留在编译器警告阶段
Swift 访问权限  // 更加细化, 能更好的够分离关注点
Swift 协议和扩展
Swift 函数和闭包 // 一等公民
```

11. HTTPS 加密与身份验证

```
答案: HTTPS 加密与身份验证部分是由TLS/SSL协议完成的
*包括两块, 第一是握手协议, 第二是记录协议, 握手协议使用非对称加密算法, 记录协议使用对称加密算法

设计目的是: 身份验证, 保密性, 完整性

TLS协议包括:
- Handshake握手协议
  - 验证通讯双方的身份
  - 交换加解密的安全套件 // 证书信任链 (使用hash算法来做验签 私钥)
    - 秘钥交换算法 ECDHE
    - 身份验证算法 RSA(非对称加密) 椭圆曲线 需要随机选择两个不相等的质数
    - 对称加密算法, 强度, 工作模式(分组)
  - 协商加密参数
- Record记录协议
  - 对称加密
    - 异或填充 ^ + padding
```

```
TLS1.2 通讯过程

1. 验证身份
2. 达成安全套件共识
3. 传递秘钥
4. 加密通讯

1 -> Client Hello        // 发送支持的安全套件列表
2 <- Server Hello        // 选择安全的套件列表, nginx中有一个表维护
3 <- Server Certificates // 发送服务端的证书
4 <- ServerKey Exchange  // 发送服务端的公钥
5 <- Server Hello Done   // 服务端结束, 仅传递信息
6 -> ClientKey Exchange  // 检查服务端证书, 发送客户端公钥
7 -> CipherSpec Exchange // 生成客户端秘钥发送给服务端 (主秘钥)
8 -> Finish              // 客户端结束, 仅传递消息
9 <- CipherSpec Exchange // 生成服务端秘钥发送给客户端 (主秘钥)
10 <- Finish             // 服务端结束, 仅传递消息

... 通过预主秘钥进行对称加密通信

TLS 1.3 因为限制了服务端的安全加密套件个数及sesson等一系列的优化, 可实现 0RTT握手
为了兼容 1.1、1.2 等“老”协议，TLS1.3 会“伪装”成 TLS1.2，新特性在“扩展”里实现；
1 -> Client Hello
  -> Key Share
  -> Early Data

2 <- Server Hello
  <- Key Share
  <- Early Data
  <- Finish
```

12. TCP, UDP 区别

|              |           TCP            |                 UDP                  |
| :----------: | :----------------------: | :----------------------------------: |
|    连接性    |         面向连接         |                无连接                |
|    可靠性    |     可靠传输,不丢包      | 不可靠传输, 尽最大努力交付, 可能丢包 |
| 首部占用空间 |            大            |                  小                  |
|   传输速率   |            慢            |                  快                  |
|   资源消耗   |            大            |                  小                  |
|   应用场景   | 浏览器,文件传输,邮件发送 |           音视频通话,直播            |
|  应用层协议  | HTTP,HTTPS,FTP,SMTP,DNS  |                 DNS                  |

```
TCP 可靠性传输: 连续ARQ + 滑动窗口 + SACK选择性确认
TCP 序号:
- 占4字节,
- 首先, 在传输过程的每一个字节都会有一个编号
- 在建立连接后, 序号代表: 这一次传给对方的TCP数据部分的第一个字节的编号
TCP 确认号:
- 占4字节,
- 在建立连接后, 确认号代表: 期望对方下一次传过来的TCP数据部分的第一个字节的编号
TCP 窗口
- 占2字节
- 这个字段有流量控制的功能, 用以告知对方下一次允许发送的数据大小(单位是字节)
TCP 超出一定的重传次数或时间, 还未收到来自对端的确认报文, 于是发送reset报文 (举例5次 看系统)
```

```
TCP 分段

为什么选择在传输层就将数据“大卸八块”分成多个段，而不是等到网络层再分片传递给数据链路层?
- 因为可以提高重传的性能
- 需要明确的是:可靠传输是在传输层进行控制的
✓ 如果在传输层不分段，一旦出现数据丢失，整个传输层的数据都得重传
✓ 如果在传输层分了段，一旦出现数据丢失，只需要重传丢失的那些段即可
```

```
TCP 流量控制

如果接收方的缓存区满了, 发送方还在疯狂着发送数据
- 接收方只能把收到的数据包丢掉, 大量的丢包会极大着浪费网络资源
- 所以要进行流量控制

什么是流量控制?
- 让发送方的发送速率不要太快, 让接收方来得及接收处理

原理:
- 通过确认报文中窗口字段来控制发送方的发送速率
- 发送方的发送窗口大小不能超过接收方给出窗口大小
- 当发送方收到接收窗口的大小为0时, 发送方就会停止发送数据

特殊情况:
- 一开始,接收方给发送方发送了0窗口的报文段
- 后面, 接收方又有了一些存储空间, 给发送方发送的非0窗口的报文段丢失了
- 发送方发送的窗口一直为零, 双方陷入僵局

解决方案:
- 当发送方收到0窗口通知时,这时发送方停止发送报文
- 并且同时开启一个定时器, 隔一段时间就发个测试报文询问接收方最新的窗口大小
- 如果接收的窗口大小还是0, 则发送方再次刷新启动定时器
```

13. TCP 拥塞控制原理

```
拥塞控制
- 防止过多的数据注入到网络中
- 避免网络中的路由器或链路过载

拥塞控制是一个全局性的过程
- 涉及到所有的主机, 路由器
- 以及与降低网络传输性能有关的所有因素
- 是大家共同努力的结果

相比而言, 流量控制是点对点通信的控制

MSS: 每个段最大的数据部分大小 (在建立连接时确定)
cwnd, congestion window: 拥塞窗口
rwnd, receive window: 接收窗口
swnd, send window: 发送窗口 swnd = min(cwnd, rwnd)
发送窗口的最大值: swnd = min(cwnd, rwnd)
- 当rwnd<cwnd, 是接收方的能力限制发送窗口的最大值
- 当cwnd<rwnd, 则是网络的拥塞限制发送窗口的最大值

方法:
- 慢开始
  - cwnd的初始值比较小, 然后随着数据包被接收方确认(收到一个ACK), cwnd就成倍增长 (指数级)
- 拥塞避免
  - ssthresh (slow start threhold): 慢开始阈值, cwnd达到阈值后, 以线性方式增加
  - 拥塞避免 (加法增大): 拥塞窗口缓慢增大, 以防止网络过早出现拥塞
  - 乘法减小: 只要网络出现拥塞, 把ssthresh减为拥塞峰值的一半, 同时执行慢开始算法 (cwnd又恢复到初始值)
  - 当网络出现频繁拥塞时, ssthresh值就下降的很快
- 快速重传
  - 接受方
    - 每收到一个失序的分组后就立即发送重复确认
    - 使发送方及时知道有分组没有到达
    - 而不要等待自己发送数据时才进行确认
  - 发送方
    - 只要连续收到三个重复确认(总共4个相同的确认), 就应该立即重传对方尚未收到的报文段
    - 而不必继续等待重传计时器到期后再重传
- 快速恢复
  - 当发送方连续收到三个重复确认, 说明网络出现拥塞
    - 就执行"乘法减小"算法, 把ssthresh减为拥塞峰值的一半
  - 与慢开始不同之处是现在不执行慢开始算法, 即cwnd现在不恢复到初始值
    - 而是把cwnd值设置为新的ssthresh值(减小后的值)
    - 然后开始执行拥塞避免算法("加法增大"), 使拥塞窗口缓慢地线性增大
```

14. SDWebImage

![](./SDWebImage/SDWebImageHighLevelDiagram.jpg)

```
- Image Manager
  - Image Cache
    - Memory
    - Disk
  - Image Loader
    - URLSession
    - Photos
```

15. 图片解码

```
Image/IO
```

16. 指针混淆

```
代码混淆

iOS程序可以通过class-dump、Hopper、IDA等获取类名、方法名、以及分析程序的执行逻辑
如果进行代码混淆，可以加大别人的分析难度

iOS的代码混淆方案
- 源码的混淆
  - 类名
  - 方法名
  - 协议名

- LLVM中间代码IR混淆
  - 自己编写Pass

- 宏定义的混淆
  - 注意点:
    - 不能混淆系统方法
    - 不能混淆init开头的初始化方法
    - 混淆属性时需要额外注意set方法
    - 如果xib, storyboard中用到了混淆的内容, 需要手动修正
    - 可以考虑把需要混淆的符号都加上前缀, 跟系统自带的符号做区分
    - 混淆过多可能会被AppStore拒绝上架, 需要说明用途

  - 建议
    - 给需要混淆的符号加上一个特定的前缀

- 字符串加密
  - 很多时候, 可执行文件中的字符串信息, 对破解者来说非常关键, 是破解的途径之一
  - 为了加大破解, 逆向难度, 可以考虑对字符串进行加密
  - 字符串的加密技术有很多种, 可以根据自己的需要自行定制算法
  - 这里举一个简单的例子
    - 对每个字符进行异或(^)处理
    - 需要使用字符串时, 对异或(^)过的字符再进行一次异或(^), 就可以获得原字符
```

17. TagPointer

```
用指针存储小对象

从64bit开始，iOS引入了Tagged Pointer技术，用于优化NSNumber、NSDate、NSString等小对象的存储

在没有使用Tagged Pointer之前， NSNumber等对象需要动态分配内存、维护引用计数等，NSNumber指针存储的是堆中NSNumber对象的地址值

使用Tagged Pointer之后，NSNumber指针里面存储的数据变成了:Tag + Data，也就是将数据直接存储在了指针中

当指针不够存储数据时，才会使用动态分配内存的方式来存储数据

objc_msgSend能识别Tagged Pointer，比如NSNumber的intValue方法，直接从指针提取数据，节省了以前的调用开销
```

18. NSString 为什么用 copy 修饰

```
答案: 保持传入字符串的的不可变性
如果传入的是NSMutableString, 使用时不会被更改, 更安全
如果用 strong 修饰的话, 可能会在外部修改内部的值
```

19. 重写 isEqual 方法，hash 方法的作用，引出 NSSet 的读写效率比较高

```
答案;

isEqual 方法用于比较元素相等
hash 方法用于减少哈希碰撞

NSSet 底层是哈希表,使用hash进行散列到对应的槽, 再使用isEqual来判断, 链表法
```

20. performselector 和直接调用方法哪个执行快

```
答案 直接调用更快, performselector会执行额外的消息发送机制

performSelector: withObject:是在iOS中的一种方法调用方式。他可以向一个对象传递任何消息，而不需要在编译的时候声明这些方法。所以这也是runtime的一种应用方式.所以performSelector和直接调用方法的区别就在与runtime。

- 直接调用编译是会自动校验。如果方法不存在，那么直接调用 在编译时候就能够发现，编译器会直接报错。
- 但是使用performSelector的话一定是在运行时候才能发现，如果此方法不存在就会崩溃。
```

21. 为什么一个线程只能有一个 runloop

```
答案:

从底层数据结构来看, runloop 持有一个 thread, 一对一关系, 主线程默认开启Runloop
从功能设计来看, 一个线程设计成只有一个RunLoop, 是因为RunLoop里面有一个无限循环.
```

22. 子线程的 runloop 开启后，如果不做任何操作，线程会被杀死吗？

```
答案: 会

如果Mode里没有任何Source0/Source1/Timer/Observer，RunLoop会立马退出
```

23. load 方法是在什么时候调用的

```
答案: load方法在runtime加载类、分类的时候调用

Category中有load方法吗?load方法是什么时候调用的?load 方法能继承吗?
- 有load方法
- load方法在runtime加载类、分类的时候调用
- load方法可以继承，但是一般情况下不会主动去调用load方法，都是让系统自动调用
*系统调用load方法是直接指针调用, 主动调用会走消息机制

load、initialize方法的区别什么?它们在category中的调用的顺序?以及出现继承时他们之间的调用过程?
- +load方法会在runtime加载类, 分类时调用
- 每个类, 分类的+load, 在程序运行过程中系统只调一次

调用顺序
1. 先调用类的+load
- 按照编译先后顺序调用 (先编译, 先调用)
- 调用子类的+load之前会调用父类的+load
2. 再调用分类的+load
- 按照编译先后顺序调用 (先编译, 先调用)
*顺序: 父类 -> 子类 -> 分类 (同级别先编译, 先调用)
```

24. initialize 方法是干嘛用的？是什么时候调用的 -

```
答案 +initialize方法在类第一次接收到消息时调用

调用顺序
- 先调用父类的+initialize, 再调用子类的+initialize
- (先初始化父类, 再初始化子类, 每个类只会初始化1次)
- +initialize和+load的很大区别是，+initialize是通过objc_msgSend进行调用的，所以有以下特点
- 如果子类没有实现+initialize，会调用父类的+initialize(所以父类的+initialize可能会被调用多次)
- 如果分类实现了+initialize，就覆盖类本身的+initialize调用
*initialize走消息机制, 所以行为同消息机制
```

25. repeated 的 NSTimer 有什么性能问题

```
答案: 可能会造成内存泄漏

NSTimer涉及到内存泄漏，主要是指在Timer中repeats为YES，
即需要间隔指定时间，重复调用方法，此时需要手动调用[self.timer invalidate]使定时器失效。

如果repeats为NO，则不存在内存泄漏问题，调用完成后，定时器会自动失效。

解决办法:

1. viewWillDisappear:手动停止
  - 需要注意在这个方法中停止，适用于不会从当前页面push出下一个页面的情况，因为如果push出下一个页面，也会调用viewWillDisappear:，可能就得不到正确的结果。
2. 重写返回方法手动停止
3. iOS10之后，系统提供的scheduledTimerWithTimeInterval:repeats:block方法
4. 去除NSTimer和当前调用对象之间的循环引用。 (weak target)
```

26. 算法：二叉树的左右子树交换代码实现；

```cpp
struct TreeNode* invertTree(struct TreeNode* root) {
    if (root == NULL) {
        return NULL;
    }
    struct TreeNode* left = invertTree(root->left);
    struct TreeNode* right = invertTree(root->right);
    root->left = right;
    root->right = left;
    return root;
}
```

27. 页面路由如何实现，如何去维护一张路由表；页面是如何去进行跳转的（runtime）；路由表中的键和值分别是什么？如何根据服务器下发的数据加载页面；

```
1. 哈希表
2. 协议
3. 中间者模式 CTMediator + 组件化使用 category Runtime(反射)解耦 使用 Proxy
4. 字典树
```

28. js 和 OC 如何调用；（js 是怎样调用 oc 的）；

```
1. UIWebView (已于iOS12淘汰)
- stringByEvaluatingJavaScript urlscheme
- window.location.href = "ios://openPhotoGallery";

2. WKWebView
- 创建WKWebViewConfiguration对象，配置各个API对应的MessageHandler。
- window.webkit.messageHandlers

JSBridge
```

29. GCD 和 NSOperation 的区别；哪一个的复用性更好；NSOperation 的队列可以 cancel 吗，里面的任务可以 cancel 吗；

```
GCD
- 旨在代替NSThread等线程技术
- 充分利用设备的多核

NSOperation
- 基于GCD(底层是GCD)
- 比GCD多了一些更简单实用的功能 (队列的暂停和恢复以及取消)
- 使用更加面向对象

NSOperation是GCD的一层封装

NSOperationQueue的复用性更好, 是GCD的面向对象的封装

NSOperation 的队列可以 cancel 吗，里面的任务可以 cancel 吗；

- 最重要的是无论是NSOperation的cancel还是NSOperationQueue的cancelAllOperations 都不会停止正在执行的operation，只能取消在队列中等待的operation
```

30. block 和 self 的循环引用；到底是如何循环引用的；

```
答案: 可以使用 __weak 进行单边打破, 或者使用__block调用手动打破

循环引用是 由于对象持有了block, block又捕获了self
```

```
Block_layout : {
  isa: (void*)
  flags: (int)
  reserved: (int)
  invoke: (void*(void *, ...)) // *FuncPtr
  descriptor: (struct Block_descriptor *) {
    reserved: (unsigned long int)
    size: (unsigned long int)
    copy: (void *(void *, void *))
    dispose: (void *(void *))
  }
  variables... (capture) // 捕获局部变量, 不捕获全局变量
}
```

```
变量捕获

auto: 值传递
static: 引用传递
全局变量: 直接访问

__block.__forwarding在copy的时候会指向堆中的__block
```

```
block的类型

- block有3种类型，可以通过调用class方法或者isa指针查看具体类型，最终都是继承自NSBlock类型
- __NSGlobalBlock__ ( 没有访问auto变量 ) 数据区 // 什么都不做
- __NSStackBlock__ ( 访问了auto变量 ) 栈区 // copy 从栈复制到堆
- __NSMallocBlock__ ( __NSMallocBlock__调用了copy ) 堆区 // copy 引用计数增加

block 的 copy
- 在ARC环境下，编译器会根据情况自动将栈上的block复制到堆上，比如以下情况
- block作为函数返回值时
- 将block赋值给__strong指针时
- block作为Cocoa API中方法名含有usingBlock的方法参数时
- block作为GCD API的方法参数时
*ARC下需要持有block, 会进行copy
```

```
block的原理是怎样的? 本质是什么?
- 封装了函数调用以及调用环境的OC对象, 就是闭包的一种实现
- 本质上也是一个OC对象, 它内部也有个isa指针

__block的作用是什么?有什么使用注意点?

block的属性修饰词为什么是copy?使用block有哪些使用注意?
- block一旦没有进行copy操作，就不会在堆上
- 使用注意:循环引用问题

block在修改NSMutableArray，需不需要添加__block?
```

31. SDWebImage 的缓存策略，是如何从缓存中 hit 一张图片的；使用了几级缓存；缓存如何满了如何处理，是否要设置过期时间；

![](./SDWebImage/SDWebImageSequenceDiagram.png)

```
使用了内存和磁盘的缓存:

- 磁盘是时间空间维度:
 - 时间维度: 默认过期时间是1周 // static const NSInteger kDefaultCacheMaxCacheAge = 60 * 60 * 24 * 7; // 1 week
 - 空间维度: [SDImageCache sharedImageCache].maxCacheSize = 1024 * 1024 * 50; // 50M// 默认是没有设置
- 内存是空间维度: 缓存满了使用LRUCache进行淘汰

SDWebImage 会在每次 APP 结束的时候执行清理任务。 清理缓存的规则分两步进行。 第一步先清除掉过期的缓存文件。 如果清除掉过期的缓存之后，空间还不够。 那么就继续按文件时间从早到晚排序，先清除最早的缓存文件，直到剩余空间达到要求。

@interface SDImageCache : NSObject

@property (assign, nonatomic) NSInteger maxCacheAge;
@property (assign, nonatomic) NSUInteger maxCacheSize;

分别在应用进入后台和结束的时候，遍历所有的缓存文件，如果缓存文件超过 maxCacheAge 中指定的时长，就会被删除掉。

同样的， maxCacheSize 控制 SDImageCache 所允许的最大缓存空间。 如果清理完过期文件后缓存空间依然没达到 maxCacheSize 的要求， 那么就会继续清理旧文件，直到缓存空间达到要求为止。

上面是 maxCacheAge 的默认值，注释上写的很清楚，缓存一周。 再来看看 maxCacheSize。 翻了一遍 SDWebImage 的代码，并没有对 maxCacheSize 设置默认值。 这就意味着 SDWebImage 在默认情况下不会对缓存空间设限制。

查询 Disk Cache 的时候有一个小插曲，就是如果 Disk Cache 查询成功，还会把得到的图片再次设置到 Memory Cache 中。

缓存策略-SDWebImageOptions

- SDWebImageRetryFailed 下载失败了会再次尝试下载 (是否要重试失败的 URL)
- SDWebImageLowPriority 当UIScrollView等正在滚动时，延迟下载图片（放置scrollView滚动卡）
- SDWebImageCacheMemoryOnly 只缓存到内存中，不缓存到硬盘上
- SDWebImageProgressiveDownload 图片会一点一点慢慢显示出来（就像浏览器显示网页上的图片一样）
- SDWebImageRefreshCached 将硬盘缓存交给系统自带的NSURLCache去处理，当同一个URL对应的图片经常更改时可以用这种策略
```

32. 讲讲 RunLoop

```
Runloop 运行逻辑

1. 通知Observers: kCFRunLoopEntry
2. 通知Observers: kCFRunLoopBeforeTimers
3. 通知Observers: kCFRunLoopBeforeSources
4. 处理Blocks
5. 处理Source0 (可能会再次处理Blocks)
6. 如果存在Source1，就跳转到第8步
7. 通知Observers: kCFRunLoopBeforeWaiting(等待消息唤醒)
8. 通知Observers: kCFRunLoopAfterWaiting(被某个消息唤醒)
  1> 处理Timer
  2> 处理GCD Async To Main Queue
  3> 处理Source1
9. 处理Blocks
10. 根据前面的执行结果，决定如何操作
  1> 回到第02步
  2> 退出Loop
11. 通知Observers: kCFRunLoopExit

```

```
Runloop 应用范畴

- 定时器(Timer)、PerformSelector
- GCD Async Main Queue
- 事件响应、手势识别、界面刷新
- 网络请求
- AutoreleasePool

Runloop 基本作用

- 保持程序的持续运行
- 处理App中的各种事件(比如触摸事件、定时器事件等)
- 节省CPU资源，提高程序性能:该做事时做事，该休息时休息

Runloop 实际应用

- 控制线程声明周期 (线程保活)
- 解决NSTimer在滑动时停止工作的问题
- 监控应用卡顿
- 性能优化

Runloop 休眠原理

- mach_msg()
- 操作系统用户态到内核态的切换
- 内核态进程切换为不活跃

//BeforeSources 和 AfterWaiting 这两个状态能够检测到是否卡顿
if (runLoopActivity == kCFRunLoopBeforeSources || runLoopActivity == kCFRunLoopAfterWaiting) {
  //将堆栈信息上报服务器的代码放到这里
} //end activity

```

33. 讲讲 iOS 动画，比如 CoreAnimation；

```
CoreAnimation翻译过来就是核心动画,一组非常强大的API，用来做动画的，非常的简单，但是效果非常绚丽
CoreAnimation是跨平台的，既可以支持IOS，也支持MAC OS
CoreAnimation执行动画是在后台，不会阻塞主线程
CoreAnimation作用在CALayer，不是UIView

动画组, 帧动画, 缓冲曲线, 贝塞尔曲线

CALayer // 基本UIView类似属性, 可使用CGImage填充, 控制颜色, 位置, 动画等
- CATextLayer // 绘制String或者AttributeString
- CAShapeLayer // 具有path属性, 与图形上下文类似属性
- CAGradientLayer // 梯度层, 颜色渐变
- CAEmitterLayer // 发射器层, 控制粒子或散列效果
- CAEAGLayer // OpenGL ES绘制的层
- CAReplicationLayer // 用来自动赋值subLayer
- CAScrollLayer // 管理可滑动区域
- CATiledLayer // 管理一副可以分割的大图
- CATransformLayer // 渲染3D Layer层级

应用使用CA有三组图层对象，每组图层对象在显示内容到屏幕上扮演的角色不同：
- 图层模型树（或称图层树）是应用交互最多的，对象在此树中存储动画的目标值，当改变图层的属性，使用这些对象中的一个
- 表现层树包含任一正在运行动画的值，此树中的对象你不能修改。但你可以用这些对象去读取当前动画的值，可利用这些值作为一个动画的起始。
- 渲染树执行实际的动画且是CA所私有的
- 当然图层组织的层级结构如视图类似，实际上，图层的初始结构与视图的初始结构相一致，有时你可以使用图层代替视图减少消耗。
- 对于图层树中的每个对象会匹配表现层树和渲染层树中的一个对象，应用主要工作的对象是图层中，但也可能通过`presentationLayer`属性访问
表现层树中的对象

动画组
关键帧动画
平移缩放旋转
```

34. 屏幕上点击一个 View，事件是如何去响应的；

```
往往在子view超出父view时，超出的部分不会响应点击事件
原因就在于：iOS的事件响应机制

iOS的事件响应机制

- 用户触摸屏幕时，UIKit会生成UIEvent对象来描述触摸事件。对象内部包含了触摸点坐标等信息。
- 通过Hit Test确定用户触摸的是哪一个UIView。这个步骤通过- (UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event方法来完成。
- 找到被触摸的UIView之后，如果它能够响应用户事件，相应的响应函数就会被调用。如果不能响应，就会沿着响应链（Responder Chain）寻找能够响应的UIResponder对象（UIView是UIResponder的子类）来响应触摸事件。

hitTest: Test确定用户触摸的是哪一个UIView
1. 从视图层级最底层的 window 开始遍历它的子 View。
2. 默认的遍历顺序是按照 UIView 中 Subviews 的逆顺序。
3. 找到 hit-TestView 之后，寻找过程就结束了。
4. 如果 View 的 userInteractionEnabled = NO，enabled = NO（ UIControl ），或者 alpha <= 0.01， hidden = YES 直接返回 nil（不再往下判断）。
5. 如果触摸点不在 view 中 (pointInSide)，直接返回 nil。
6. 如果触摸点在 view 中，逆序遍历它的子 View ，重复上面的过程，如果子View没有subView了，那子View就是hit-TestView。
7. 如果 view 的 子view 都返回 nil（都不是 hit-TestVeiw ），那么返回自身（自身是 hit-TestView ）。

pointInSide: 点击的点是否在矩形框内

*事件捕获是从 Window 开始逐级遍历找到 View
*事件响应式从 View 开始调用next响应者 到 Window -> Application -> AppDelegate
```

35. 深拷贝与浅拷贝；-
36. 属性有哪些修饰符 -
37. 将一个 NSArray 赋值给一个 copy 修饰的 NSMutableArray 属性，然后尝试向这个可变数组添加对象，会发生什么？ -
38. Category 同名方法 -
39. Extention 可以有多个吗？
40. Category 多个同名方法怎么进行 Method swizzing -
41. GCD 串行队列和并行队列执行顺序分析 -
42. NSOperator 执行顺序分析，maxConcurrent 为 2 或者 1 两种情况 -
43. 100 亿个数求 top k，算法复杂度，怎么在算法最优的情况下再快 100 倍？-
44. KVO 的实现原理，一个类的多次 kvo 会生成多个新类吗？是直接就对所有的属性都生成 kvo 的方法吗？-
45. http 返回码有哪些，206 返回码，断点续传
46. https 握手原理，能确保安全吗 -
47. runloop 原理，几种 mode -
48. autoreleasepool 原理？如果对一个对象写了多次 autorelease，会怎样？ -
49. weak table 是用的什么数据结构
50. block 几种内存类型，如何捕获变量
51. 注意 copy 和 mutableCopy 方法，有陷阱，
52. @synchronized(xxx)的实现

```
- @synchronized // @synchronized是对mutex递归锁的封装
@synchronized(obj)内部会生成obj对应的递归锁，然后进行加锁、解锁操作
```

53. atomic 实现原理。

```
atomic

atomic用于保证属性setter、getter的原子性操作，相当于在getter和setter内部加了线程同步的锁
它并不能保证使用属性的过程是线程安全的
*锁的粒度的把握

func foo() { // foo 函数没加锁, 不能保证使用属性的过程是线程安全的
  property.read()
  property.write()
}

func read() {
  lock // 自旋锁
  read()
  unlock // 自旋锁
}

func write() {
  lock // 自旋锁
  write()
  unlock // 自旋锁
}
```

54. 实现 Power()函数
55. TCP 的断包粘包如何避免
56. OC 消息机制
57. iOS 启动流程
