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
      - kCFRunLoopBeforeWaiting  // 即将进入休眠 + UI刷新 + Autorealease pool
      - kCFRunLoopAfterWaiting   // 刚从休眠中唤醒
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

```

```
autorelease 的释放时机

答案: 当 RunLoop 处于 kCFRunLoopBeforeWaiting 时释放
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
#include <iostream>
#include <string>

using namespace std;

class Solution {
public:
    int myAtoi(string str) {
        unsigned long len = str.length();

        // 去除前导空格
        int index = 0;
        while (index < len) {
            if (str[index] != ' ') {
                break;
            }
            index++;
        }

        if (index == len) {
            return 0;
        }

        int sign = 1;
        // 处理第 1 个非空字符为正负符号，这两个判断需要写在一起
        if (str[index] == '+') {
            index++;
        } else if (str[index] == '-') {
            sign = -1;
            index++;
        }

        // 根据题目限制，只能使用 int 类型
        int res = 0;
        while (index < len) {
            char curChar = str[index];
            if (curChar < '0' || curChar > '9') {
                break;
            }

            int num = (curChar - '0');

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
};
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
9. 自旋锁, 互斥锁
10. Swift, OC 差异 -
11. HTTPS 加密与身份验证
12. TCP, UDP 区别 -
13. TCP 拥塞控制原理
14. SDWebImage -
15. 图片解码 -
16. 指针混淆 -
17. TagPointer
18. NSString 为什么用 copy 修饰 -
19. 重写 isEqual 方法，hash 方法的作用，引出 NSSet 的读写效率比较高 -
20. performselector 和直接调用方法哪个执行快
21. 为什么一个线程只能有一个 runloop
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
26. 算法：二叉树的左右子树交换代码实现； -
27. 页面路由如何实现，如何去维护一张路由表；页面是如何去进行跳转的（runtime）；路由表中的键和值分别是什么？如何根据服务器下发的数据加载页面； -
28. js 和 OC 如何调用；（js 是怎样调用 oc 的）；-
29. GCD 和 NSOperation 的区别；哪一个的复用性更好；NSOperation 的队列可以 cancel 吗，里面的任务可以 cancel 吗；
30. block 和 self 的循环引用；到底是如何循环引用的；-
31. SDWebImage 的缓存策略，是如何从缓存中 hit 一张图片的；使用了几级缓存；缓存如何满了如何处理，是否要设置过期时间； -
32. 讲讲 RunLoop -
33. 讲讲 iOS 动画，比如 CoreAnimation； -
34. 屏幕上点击一个 View，事件是如何去响应的； -
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
53. atomic 实现原理。
54. 实现 Power()函数
55. TCP 的断包粘包如何避免
