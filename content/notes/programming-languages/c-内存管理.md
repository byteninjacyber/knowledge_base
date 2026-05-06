---
title: "C++ 内存管理"
date: 2026-05-06
tags: [cpp, memory-management, raii, smart-pointer, allocator]
summary: "深入分析 C++ 内存管理机制：从栈/堆分配到智能指针、内存池，附性能对比实验"
ai_generated: false
---

# C++ 内存管理

## 核心问题

C++ 给了程序员直接操控内存的能力，代价是你必须回答三个问题：

1. **谁分配？** （栈 vs 堆 vs 自定义分配器）
2. **谁释放？** （手动 vs RAII vs GC-like 引用计数）
3. **生命周期如何传递？** （所有权语义 vs 借用语义）

答错任何一个 = 内存泄漏、悬垂指针、double free。

---

## 一、栈 vs 堆：不只是速度的区别

### 栈分配

```cpp
void foo() {
    int arr[1024];          // 4KB，栈上分配
    std::array<int, 1024> a; // 同上，类型安全
}   // 函数返回时自动释放，零成本
```

栈分配 = 移动栈指针（1 条 `sub rsp, N` 指令），**没有系统调用，没有锁竞争**。

### 堆分配

```cpp
void bar() {
    int* p = new int[1024];  // malloc → mmap/brk → 内核态切换
    delete[] p;
}
```

堆分配的隐藏成本：
- `malloc` 需要遍历 free list 或 bin
- 多线程下有锁竞争（ptmalloc2 的 arena 锁）
- 内存碎片导致 TLB miss 增加

### 关键思考

> 不是"堆慢所以用栈"，而是**栈的生命周期是确定的（函数作用域），堆的生命周期是动态的**。选择依据是生命周期需求，不是性能。

---

## 二、RAII — C++ 内存管理的基石

RAII (Resource Acquisition Is Initialization) 的本质：**把资源生命周期绑定到对象生命周期**。

```cpp
class Buffer {
    uint8_t* data_;
    size_t size_;
public:
    explicit Buffer(size_t n) : data_(new uint8_t[n]), size_(n) {}
    ~Buffer() { delete[] data_; }

    // 禁止拷贝，避免 double free
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    // 允许移动，转移所有权
    Buffer(Buffer&& other) noexcept : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }
};
```

**为什么 RAII 比 GC 更适合系统编程？**

- 析构时机确定 → 可以管理文件句柄、锁、网络连接（不只是内存）
- 零运行时开销 → 没有 GC pause
- 编译期检查 → move 语义让所有权转移可追踪

---

## 三、智能指针：语义不同，用途不同

| 类型 | 所有权语义 | 引用计数 | 线程安全 | 典型场景 |
|---|---|---|---|---|
| `unique_ptr` | 独占 | 无 | N/A | 工厂函数返回值、成员变量 |
| `shared_ptr` | 共享 | 有（atomic） | 引用计数是 | 缓存、观察者模式 |
| `weak_ptr` | 观察 | 不增加 | 同 shared | 打破循环引用、缓存探测 |

### Demo: shared_ptr 的隐藏成本

```cpp
#include <memory>
#include <chrono>
#include <iostream>

struct Payload {
    char data[64];
};

void bench_unique() {
    for (int i = 0; i < 1000000; ++i) {
        auto p = std::make_unique<Payload>();
    }
}

void bench_shared() {
    for (int i = 0; i < 1000000; ++i) {
        auto p = std::make_shared<Payload>();
    }
}

void bench_shared_copy() {
    auto p = std::make_shared<Payload>();
    for (int i = 0; i < 1000000; ++i) {
        auto copy = p;  // 原子引用计数 +1/-1
    }
}

int main() {
    using Clock = std::chrono::high_resolution_clock;

    auto t1 = Clock::now();
    bench_unique();
    auto t2 = Clock::now();
    bench_shared();
    auto t3 = Clock::now();
    bench_shared_copy();
    auto t4 = Clock::now();

    auto ms = [](auto d) {
        return std::chrono::duration_cast<std::chrono::milliseconds>(d).count();
    };

    std::cout << "unique_ptr create/destroy: " << ms(t2-t1) << " ms\n";
    std::cout << "shared_ptr create/destroy: " << ms(t3-t2) << " ms\n";
    std::cout << "shared_ptr copy (atomic):  " << ms(t4-t3) << " ms\n";
}
```

### 实验结果 (g++ -O2, AMD Ryzen 7 5800X)

```
unique_ptr create/destroy: 18 ms
shared_ptr create/destroy: 35 ms
shared_ptr copy (atomic):  12 ms
```

**分析：**
- `shared_ptr` 创建比 `unique_ptr` 慢约 2x → 需要额外分配控制块（`make_shared` 优化为一次分配）
- `shared_ptr` 拷贝的 12ms 全是原子操作开销 → 多线程下会更严重（cache line bouncing）

**结论：** 默认用 `unique_ptr`，只在真正需要共享所有权时用 `shared_ptr`。

---

## 四、内存池 — 当 malloc 成为瓶颈

### 场景

高频创建/销毁固定大小对象（网络包、AST 节点、游戏 Entity）。

### 实现：简单的 free list 池

```cpp
template <typename T, size_t BlockSize = 4096>
class MemoryPool {
    union Slot {
        T element;
        Slot* next;
    };

    Slot* free_list_ = nullptr;
    std::vector<void*> blocks_;

    void allocate_block() {
        size_t count = BlockSize / sizeof(Slot);
        auto* block = static_cast<Slot*>(::operator new(BlockSize));
        blocks_.push_back(block);

        for (size_t i = 0; i < count - 1; ++i) {
            block[i].next = &block[i + 1];
        }
        block[count - 1].next = free_list_;
        free_list_ = block;
    }

public:
    MemoryPool() { allocate_block(); }

    ~MemoryPool() {
        for (auto* b : blocks_) ::operator delete(b);
    }

    T* allocate() {
        if (!free_list_) allocate_block();
        Slot* slot = free_list_;
        free_list_ = slot->next;
        return reinterpret_cast<T*>(slot);
    }

    void deallocate(T* p) {
        auto* slot = reinterpret_cast<Slot*>(p);
        slot->next = free_list_;
        free_list_ = slot;
    }
};
```

### 对比实验

```cpp
struct Node { int val; Node* left; Node* right; };

// 标准 new/delete
void bench_standard(int n) {
    std::vector<Node*> nodes(n);
    for (int i = 0; i < n; ++i) nodes[i] = new Node{i, nullptr, nullptr};
    for (int i = 0; i < n; ++i) delete nodes[i];
}

// 内存池
void bench_pool(int n) {
    MemoryPool<Node> pool;
    std::vector<Node*> nodes(n);
    for (int i = 0; i < n; ++i) {
        nodes[i] = pool.allocate();
        new (nodes[i]) Node{i, nullptr, nullptr};  // placement new
    }
    for (int i = 0; i < n; ++i) {
        nodes[i]->~Node();
        pool.deallocate(nodes[i]);
    }
}
```

### 实验结果 (1,000,000 次分配/释放)

```
standard new/delete:  45 ms
memory pool:          8 ms   (5.6x faster)
```

**为什么快？**
- 无 malloc 元数据开销（每次 malloc 额外 16 字节 header）
- 无 free list 搜索（池的 free list 是 O(1) pop/push）
- 内存连续 → cache friendly

---

## 五、常见陷阱与防御

### 1. 悬垂引用

```cpp
std::string_view dangerous() {
    std::string s = "hello";
    return s;  // s 析构后 string_view 指向无效内存
}
```

**防御：** 用 `-fsanitize=address` 编译，ASan 会在运行时捕获。

### 2. 循环引用

```cpp
struct A {
    std::shared_ptr<B> b;
};
struct B {
    std::shared_ptr<A> a;  // 循环！永远不会释放
};
```

**防御：** 其中一方用 `weak_ptr`。

### 3. 异常安全

```cpp
void unsafe(int* a, int* b) {
    a = new int(1);
    b = new int(2);  // 如果这里抛异常，a 泄漏
}

void safe() {
    auto a = std::make_unique<int>(1);
    auto b = std::make_unique<int>(2);  // 异常安全
}
```

---

## 六、现代 C++ 内存管理决策树

```
需要动态分配？
├── 否 → 用栈/std::array
└── 是 → 谁拥有这块内存？
    ├── 单一拥有者 → unique_ptr
    ├── 多个拥有者 → shared_ptr
    └── 需要观察但不拥有 → weak_ptr 或 raw pointer（不负责释放）
        └── 性能敏感？高频分配？
            └── 是 → 内存池 / arena allocator
```

---

## 延伸阅读

- [[RAII 模式详解]]
- [[C++ Move 语义]]
- [[自定义 Allocator 实战]]
- [[Valgrind 和 ASan 使用指南]]
