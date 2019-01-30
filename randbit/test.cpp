#include <iostream>
#include <cstdint>
#include <random>

uint32_t rbs(double p, std::mt19937 &mt){
  std::uniform_real_distribution<> ud(0.0,1.0);
  uint32_t v;
  for(int i=0;i<32;i++){
    if (ud(mt) < p){
      v |= (1<<i); 
    }
  }
  return v;
}

void show(uint32_t v){
  for(int i=0;i<32;i++){
    std::cout << (v&1);
    v >>= 1;
  }
  std::cout << std::endl;
}


int main(){
  std::mt19937 mt(1);
  for(int i=0;i<10;i++){
    show(rbs(0.5,mt));
  }
}
