
# 定数配列がからんだ定数畳み込み最適化

# はじめに

配列を定数(`const`)として宣言した場合や、事実上定数とみなせる場合、コンパイラが定数畳み込み最適化をできるか確認する。

# 定数畳み込みについて

コンパイラの最適化には様々なものがあるが、その最も簡単なものに「定数畳み込み」がある。これは、コンパイル時に定数であることがわかっている式を単純化するものだ。

例えば、こんなコードを見てみる。

```cpp:test.cpp
const double G = 9.8;
const double dt = 0.01;
const int N = 10000;

void func(double v[N]) {
  for (int i = 0; i < N; i++) {
    v[i] += G * dt;
  }
}
```

速度の配列`v`を受け取り、そのすべての要素に重力定数`G`と時間刻み`dt`の積`G*dt`を加算するコードだ。このコードを見て、「毎回メモリから`G`と`dt`の値を取ってきて、掛け算しては足す」という動作をする、と考える人はもういないだろう。多くの人は「コンパイラが`G`と`dt`の積を作って、それをレジスタに乗せて、ループ中は使い回す」という最適化をすると期待すると思う。

実際、現代のコンパイラはこれをちゃんと最適化する。上記のコードを`g++ -O3 -S`でコンパイルすると、こんなアセンブリを吐く。

```nasm:test.s
func(double*):
LFB0:
	movapd	lC0(%rip), %xmm1
	leaq	80000(%rdi), %rax
	.align 4,0x90
L2:
	movq	(%rdi), %xmm0
	addq	$16, %rdi
	movhpd	-8(%rdi), %xmm0
	addpd	%xmm1, %xmm0
	movlpd	%xmm0, -16(%rdi)
	movhpd	%xmm0, -8(%rdi)
	cmpq	%rdi, %rax
	jne	L2
	ret
```

最初に`lC0`からロードしているのが`G * dt`の値で、それはこうなっている。

```nasm:
lC0:
	.long	721554506
	.long	1069094535
	.long	721554506
	.long	1069094535
```

これは、`0.098`という倍精度実数を二つ並べたものだ。確認してみよう。

```rb
[0.098].pack("d").unpack("I!*") #=> [721554506, 1069094535]
```

なぜ二つかというと、xmmに二つロードしてSIMD化するためである。`-mavx2`オプションをつければymmも使うため、4つデータを並べるようになる。

繰り返しになるが、プログラマは「これくらいの最適化はしてくれるだろう」と期待してプログラムを組む。では、定数がもう少しややこしい形をしていたら？例えば配列の形で与えても、コンパイラはそれを見抜けるだろうか？というのが本稿の本題である。

# 配列の内積

こんなコードを考えよう。

```cpp:array1.cpp
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
```

`func`は4次元の整数ベクトルを受け取り、(1,2,3,4)というベクトルと内積をとった結果を返す関数だ。このプログラムでは(5,6,7,8)との内積をとっているので、結果は70になるが、GCCはそれは見抜くことはできず、愚直に計算をする。

しかし、配列が定数であるという情報を与えてやると、即値を返せるようになる。

```cpp:array2.cpp
#include <cstdio>
const int a[] = {1, 2, 3, 4}; // ←constをつけた

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
```

これを`g++ -O3 -S`でコンパイルするとこうなる。

```nasm
_main:
LFB2:
  subq  $8, %rsp
LCFI0:
  movl  $70, %esi
  xorl  %eax, %eax
  leaq  lC0(%rip), %rdi
  call  _printf
  xorl  %eax, %eax
  addq  $8, %rsp
LCFI1:
  ret
```

コンパイラは結果が70であることを見抜いて、関数`func`を即値70で置き換えてしまう。

また、配列`a`がグローバル変数ではなく、ローカル変数であれば、`const`をつけなくても即値で返せるようになる。

```cpp:array2.cpp
#include <cstdio>

int func(int b[4]) {
  int a[] = {1, 2, 3, 4}; // ←ローカル変数にした
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
```

ちなみに、clang++もg++と同様な最適化ができたが、インテルコンパイラは全部ダメだった。

# どこまでいけるのか？

さて、某slackでこの話をしたら、「ループアンロールとのからみだと思うが、ループ数が増えたらどうなるんだろう？」という疑問が出てきた。試してみよう。こんなスクリプトを書く。

```ruby
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
```
