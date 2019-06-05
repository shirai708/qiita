n = ARGV[0].to_i
s = (1..n).to_a.map { |i| i.to_s }.join(",")
s = "{" + s + "}"

puts <<"EOS"
#include <cstdio>
const int N = #{n};
const int a[] = #{s};

int func(int b[N]) { 
  int sum = 0;
  for (int i = 0; i < N; i++) { 
    sum += a[i] * b[i];
  } 
  return sum;
}

int main() { 
  int b[] = #{s};
  printf("%d\\n", func(b));
}
EOS
