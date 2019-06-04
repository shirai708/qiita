#include <cstdio>
int a[] = {1, 2, 3, 4};

int func(int b[4]) {
  int sum = 0;
  for (int i = 0; i < 4; i++) {
    sum += a[i] * b[i];
  }
  return sum;
}

int main() {
  int b[] = {5, 6, 7, 8};
  printf("%d\n", func(b));
}
