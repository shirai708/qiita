#include <iostream>

int a = 10;

void func(){
  a = 20;
}

int main(){
  func();
  std::cout << a << std::endl;
}
