#include <iostream>

void func1() {
  static int a = 10;
  struct {
    void operator()() {
      a = 20;
    }
  } func2;
  func2();
  std::cout << a << std::endl;
}

int main() {
  func1();
}
