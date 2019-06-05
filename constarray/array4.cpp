#include <cstdio>

int func(int b[4]) {
  const int a[] = {1, 2, 3, 4};
  int sum = 0;
  for (int i = 0; i < 4; i++) {
    sum += a[i] * b[i];
  }
  return sum;
}

int main() {
  int b[] = {};
  printf("%d\n", func(b));
}
