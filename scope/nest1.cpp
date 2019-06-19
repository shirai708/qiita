#include <iostream>

void func1(){
  struct {
    void operator()(){
      std::cout << "Hello func2" << std::endl;
    }
  }func2;
  func2();
}

int main(){
  func1();
}
