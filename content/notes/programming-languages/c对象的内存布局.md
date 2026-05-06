---
title: "C++对象的内存布局"
date: 2026-05-06
tags:
  - cpp
  - 内存布局
  - 虚函数
  - 面向对象
summary: "深入分析C++对象在内存中的布局，涵盖单一继承、多重继承、重复继承、虚拟继承等场景下的虚函数表和成员变量排列"
ai_generated: false
---

## 前言

07年12月，我写了一篇《C++虚函数表解析》的文章，引起了大家的兴趣。有很多朋友对我的文章留了言，有鼓励我的，有批评我的，还有很多问问题的。我在这里一并对大家的留言表示感谢。这也是我为什么再写一篇续言的原因。因为，在上一篇文章中，我用了的示例都是非常简单的，主要是为了说明一些机理上的问题，也是为了图一些表达上方便和简单。不想，这篇文章成为了打开C++对象模型内存布局的一个引子，引发了大家对C++对象的更深层次的讨论。当然，我之前的文章还有很多方面没有涉及，从我个人感觉下来，在谈论虚函数表里，至少有以下这些内容没有涉及：

1. 有成员变量的情况。
2. 有重复继承的情况。
3. 有虚拟继承的情况。
4. 有钻石型虚拟继承的情况。

这些都是本篇文章需要向大家说明的东西。所以，这篇文章将会是《C++虚函数表解析》的一个续篇，也是一篇高级进阶的文章。

## 对象的影响因素

简而言之，我们一个类可能会有如下的影响因素：

1. 成员变量
2. 虚函数（产生虚函数表）
3. 单一继承（只继承于一个类）
4. 多重继承（继承多个类）
5. 重复继承（继承的多个父类中其父类有相同的超类）
6. 虚拟继承（使用virtual方式继承，为了保证继承后父类的内存布局只会存在一份）

上述的东西通常是C++这门语言在语义方面对对象内部的影响因素，当然，还会有编译器的影响（比如优化），还有字节对齐的影响。在这里我们都不讨论，我们只讨论C++语言上的影响。

本篇文章着重讨论下述几个情况下的C++对象的内存布局情况：

1. 单一的一般继承（带成员变量、虚函数、虚函数覆盖）
2. 单一的虚拟继承（带成员变量、虚函数、虚函数覆盖）
3. 多重继承（带成员变量、虚函数、虚函数覆盖）
4. 重复多重继承（带成员变量、虚函数、虚函数覆盖）
5. 钻石型的虚拟多重继承（带成员变量、虚函数、虚函数覆盖）

## 知识复习

我们简单地复习一下，我们可以通过对象的地址来取得虚函数表的地址，如：

```cpp
typedef void(*Fun)(void);
Base b;
Fun pFun = NULL;
cout << "虚函数表地址：" << (int*)(&b) << endl;
cout << "虚函数表 - 第一个函数地址：" << (int*)*(int*)(&b) << endl;

// Invoke the first virtual function
pFun = (Fun)*((int*)*(int*)(&b));
pFun();
```

我们同样可以用这种方式来取得整个对象实例的内存布局。因为这些东西在内存中都是连续分布的，我们只需要使用适当的地址偏移量，我们就可以获得整个内存对象的布局。

本篇文章中的例程或内存布局主要使用如下编译器和系统：

1. Windows XP 和 VC++ 2003
2. Cygwin 和 G++ 3.4.4

## 单一的一般继承

下面，我们假设有如下所示的一个继承关系：

- Parent → Child → GrandChild

请注意，在这个继承关系中，父类，子类，孙子类都有自己的一个成员变量。而子类覆盖了父类的`f()`方法，孙子类覆盖了子类的`g_child()`及其超类的`f()`。

源程序如下所示：

```cpp
class Parent {
public:
    int iparent;
    Parent():iparent(10) {}
    virtual void f() { cout << "Parent::f()" << endl; }
    virtual void g() { cout << "Parent::g()" << endl; }
    virtual void h() { cout << "Parent::h()" << endl; }
};

class Child : public Parent {
public:
    int ichild;
    Child():ichild(100) {}
    virtual void f() { cout << "Child::f()" << endl; }
    virtual void g_child() { cout << "Child::g_child()" << endl; }
    virtual void h_child() { cout << "Child::h_child()" << endl; }
};

class GrandChild : public Child {
public:
    int igrandchild;
    GrandChild():igrandchild(1000) {}
    virtual void f() { cout << "GrandChild::f()" << endl; }
    virtual void g_child() { cout << "GrandChild::g_child()" << endl; }
    virtual void h_grandchild() { cout << "GrandChild::h_grandchild()" << endl; }
};
```

测试程序：

```cpp
typedef void(*Fun)(void);
GrandChild gc;
int** pVtab = (int**)&gc;

cout << "[0] GrandChild::_vptr->" << endl;
for (int i=0; (Fun)pVtab[0][i]!=NULL; i++) {
    pFun = (Fun)pVtab[0][i];
    cout << "    ["<<i<<"] ";
    pFun();
}
cout << "[1] Parent.iparent = " << (int)pVtab[1] << endl;
cout << "[2] Child.ichild = " << (int)pVtab[2] << endl;
cout << "[3] GrandChild.igrandchild = " << (int)pVtab[3] << endl;
```

运行结果（在VC++ 2003和G++ 3.4.4下）：

```
[0] GrandChild::_vptr->
    [0] GrandChild::f()
    [1] Parent::g()
    [2] Parent::h()
    [3] GrandChild::g_child()
    [4] Child::h_child()
    [5] GrandChild::h_grandchild()
[1] Parent.iparent = 10
[2] Child.ichild = 100
[3] GrandChild.igrandchild = 1000
```

**内存布局：**

```
+------------------+
| _vptr            | --> [GrandChild::f(), Parent::g(), Parent::h(),
|                  |      GrandChild::g_child(), Child::h_child(),
|                  |      GrandChild::h_grandchild()]
+------------------+
| Parent::iparent  | = 10
+------------------+
| Child::ichild    | = 100
+------------------+
| GrandChild::     |
| igrandchild      | = 1000
+------------------+
```

**结论：**

1. 虚函数表在最前面的位置。
2. 成员变量根据其继承和声明顺序依次放在后面。
3. 在单一的继承中，被overwrite的虚函数在虚函数表中得到了更新。

## 多重继承

假设有下面这样一个类的继承关系。子类只overwrite了父类的`f()`函数，而还有一个是自己的函数`g1()`。每个类中都有一个自己的成员变量：

```cpp
class Base1 {
public:
    int ibase1;
    Base1():ibase1(10) {}
    virtual void f() { cout << "Base1::f()" << endl; }
    virtual void g() { cout << "Base1::g()" << endl; }
    virtual void h() { cout << "Base1::h()" << endl; }
};

class Base2 {
public:
    int ibase2;
    Base2():ibase2(20) {}
    virtual void f() { cout << "Base2::f()" << endl; }
    virtual void g() { cout << "Base2::g()" << endl; }
    virtual void h() { cout << "Base2::h()" << endl; }
};

class Base3 {
public:
    int ibase3;
    Base3():ibase3(30) {}
    virtual void f() { cout << "Base3::f()" << endl; }
    virtual void g() { cout << "Base3::g()" << endl; }
    virtual void h() { cout << "Base3::h()" << endl; }
};

class Derive : public Base1, public Base2, public Base3 {
public:
    int iderive;
    Derive():iderive(100) {}
    virtual void f() { cout << "Derive::f()" << endl; }
    virtual void g1() { cout << "Derive::g1()" << endl; }
};
```

运行结果：

```
[0] Base1::_vptr->
    [0] Derive::f()
    [1] Base1::g()
    [2] Base1::h()
    [3] Derive::g1()
    [4] 00000000
[1] Base1.ibase1 = 10
[2] Base2::_vptr->
    [0] Derive::f()
    [1] Base2::g()
    [2] Base2::h()
    [3] 00000000
[3] Base2.ibase2 = 20
[4] Base3::_vptr->
    [0] Derive::f()
    [1] Base3::g()
    [2] Base3::h()
    [3] 00000000
[5] Base3.ibase3 = 30
[6] Derive.iderive = 100
```

**内存布局：**

```
+------------------+
| Base1::_vptr     | --> [Derive::f(), Base1::g(), Base1::h(), Derive::g1()]
+------------------+
| Base1::ibase1    | = 10
+------------------+
| Base2::_vptr     | --> [Derive::f(), Base2::g(), Base2::h()]
+------------------+
| Base2::ibase2    | = 20
+------------------+
| Base3::_vptr     | --> [Derive::f(), Base3::g(), Base3::h()]
+------------------+
| Base3::ibase3    | = 30
+------------------+
| Derive::iderive  | = 100
+------------------+
```

**结论：**

1. 每个父类都有自己的虚表。
2. 子类的成员函数被放到了第一个父类的表中。
3. 内存布局中，其父类布局依次按声明顺序排列。
4. 每个父类的虚表中的`f()`函数都被overwrite成了子类的`f()`。这样做就是为了解决不同的父类类型的指针指向同一个子类实例，而能够调用到实际的函数。

## 重复继承

所谓重复继承，也就是某个基类被间接地重复继承了多次。

继承关系：B → B1, B → B2, B1+B2 → D

```cpp
class B {
public:
    int ib;
    char cb;
public:
    B():ib(0),cb('B') {}
    virtual void f() { cout << "B::f()" << endl; }
    virtual void Bf() { cout << "B::Bf()" << endl; }
};

class B1 : public B {
public:
    int ib1;
    char cb1;
public:
    B1():ib1(11),cb1('1') {}
    virtual void f() { cout << "B1::f()" << endl; }
    virtual void f1() { cout << "B1::f1()" << endl; }
    virtual void Bf1() { cout << "B1::Bf1()" << endl; }
};

class B2 : public B {
public:
    int ib2;
    char cb2;
public:
    B2():ib2(12),cb2('2') {}
    virtual void f() { cout << "B2::f()" << endl; }
    virtual void f2() { cout << "B2::f2()" << endl; }
    virtual void Bf2() { cout << "B2::Bf2()" << endl; }
};

class D : public B1, public B2 {
public:
    int id;
    char cd;
public:
    D():id(100),cd('D') {}
    virtual void f() { cout << "D::f()" << endl; }
    virtual void f1() { cout << "D::f1()" << endl; }
    virtual void f2() { cout << "D::f2()" << endl; }
    virtual void Df() { cout << "D::Df()" << endl; }
};
```

运行结果（GCC 3.4.4）：

```
[0] D::B1::_vptr->
    [0] D::f()
    [1] B::Bf()
    [2] D::f1()
    [3] B1::Bf1()
    [4] D::f2()
    [5] D::Df()
[1] B::ib = 0
[2] B::cb = B
[3] B1::ib1 = 11
[4] B1::cb1 = 1
[5] D::B2::_vptr->
    [0] D::f()
    [1] B::Bf()
    [2] D::f2()
    [3] B2::Bf2()
[6] B::ib = 0
[7] B::cb = B
[8] B2::ib2 = 12
[9] B2::cb2 = 2
[10] D::id = 100
[11] D::cd = D
```

**关键结论：**

最顶端的父类B其成员变量存在于B1和B2中，并被D给继承下去了。而在D中，其有B1和B2的实例，于是**B的成员在D的实例中存在两份**，一份是B1继承而来的，另一份是B2继承而来的。

```cpp
D d;
d.ib = 0;           // 二义性错误
d.B1::ib = 1;       // 正确
d.B2::ib = 2;       // 正确
```

注意，上面例程中的最后两条语句存取的是两个变量。虽然我们消除了二义性的编译错误，但B类在D中还是有两个实例，这种继承造成了数据的重复，我们叫这种继承为**重复继承**。重复的基类数据成员可能并不是我们想要的。所以，C++引入了**虚基类**的概念。

## 钻石型多重虚拟继承

虚拟继承的出现就是为了解决重复继承中多个间接父类的问题的。钻石型的结构是其最经典的结构。

只需要把B1和B2继承B的语法中加上`virtual`关键字，就成了虚拟继承：

```cpp
class B {……};
class B1 : virtual public B {……};
class B2 : virtual public B {……};
class D : public B1, public B2 {……};
```

### 单一虚拟继承（B1对象布局）

运行结果对比：

**GCC 3.4.4：**
```
[0] B1::_vptr ->
    [0] B1::f()
    [1] B1::f1()
    [2] B1::Bf1()
[1] B1::ib1 = 11
[2] B1::cb1 = 1
[3] B::_vptr ->
    [0] B1::f()
    [1] B::Bf()
[4] B::ib = 0
[5] B::cb = B
```

**VC++ 2003：**
```
[0] B1::_vptr->
    [0] B1::f1()
    [1] B1::Bf1()
[1] = 0x00454310 （该地址取值后是-4）
[2] B1::ib1 = 11
[3] B1::cb1 = 1
[4] = 0x00000000
[5] B::_vptr->
    [0] B1::f()
    [1] B::Bf()
[6] B::ib = 0
[7] B::cb = B
```

### 钻石型虚拟继承（D对象布局）

**GCC 3.4.4：**
```
[0] B1::_vptr ->
    [0] D::f()
    [1] D::f1()
    [2] B1::Bf1()
    [3] D::f2()
    [4] D::Df()
[1] B1::ib1 = 11
[2] B1::cb1 = 1
[3] B2::_vptr ->
    [0] D::f()
    [1] D::f2()
    [2] B2::Bf2()
[4] B2::ib2 = 12
[5] B2::cb2 = 2
[6] D::id = 100
[7] D::cd = D
[8] B::_vptr ->
    [0] D::f()
    [1] B::Bf()
[9] B::ib = 0
[10] B::cb = B
```

**VC++ 2003：**
```
[0] D::B1::_vptr->
    [0] D::f1()
    [1] B1::Bf1()
    [2] D::Df()
[1] = 0x0013FDC4 （该地址取值后是-4）
[2] B1::ib1 = 11
[3] B1::cb1 = 1
[4] D::B2::_vptr->
    [0] D::f2()
    [1] B2::Bf2()
[5] = 0x04539260 （该地址取值后是-4）
[6] B2::ib2 = 12
[7] B2::cb2 = 2
[8] D::id = 100
[9] D::cd = D
[10] = 0x00000000
[11] D::B::_vptr->
    [0] D::f()
    [1] B::Bf()
[12] B::ib = 0
[13] B::cb = B
```

**关键结论：**

1. 无论是GCC还是VC++，除了一些细节上的不同，其大体上的对象布局是一样的——先是B1，然后是B2，接着是D，而B这个超类的实例都放在**最后的位置**。
2. 关于虚函数表，尤其是第一个虚表，GCC和VC++有很重大的不一样。但VC++的虚表比较清晰和有逻辑性。
3. VC++和GCC都把B这个超类放到了最后，而VC++有一个NULL分隔符把B和B1/B2的布局分开。
4. VC++中的内存布局有指针（取值为-4），理论上应该是指向B类实例的偏移信息（这是保证重复的父类只有一个实例的技术）。
5. GCC的内存布局中在B1和B2中则没有显式指向B的指针，编译器可以通过计算B1和B2的size而得出B的偏移量。

## 结束语

C++这门语言是一门比较复杂的语言，对于程序员来说，我们似乎永远摸不清楚这门语言背着我们在干了什么。需要熟悉这门语言，我们就必需要了解C++里面的那些东西，需要我们去了解它后面的内存对象。这样我们才能真正的了解C++，从而能够更好的使用C++这门最难的编程语言。

## 参考文献

- 原文作者：陈皓 (haoel@hotmail.com)
- C++ 对象的内存布局（上）
- C++ 对象的内存布局（下）
