#include <iostream>

template <class T>
struct hoge {
};

template <class T>
struct subhoge : public hoge<T> {
  void func() {
    std::cout << this->a << std::endl;
  }
};

template <>
struct hoge<int> {
  int a;
  hoge()
      : a(10) {
  }
};

int main() {
  subhoge<int> sh;
  sh.func();
}
