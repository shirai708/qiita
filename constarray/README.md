
# 定数配列がからんだ定数畳み込み最適化

# はじめに

配列を定数(`const`)として宣言した場合や、事実上定数とみなせる場合、コンパイラが定数畳み込み最適化をできるか確認する。

# 定数畳み込みについて

コンパイラの最適化には様々なものがあるが、その最も簡単なものに「定数畳み込み」がある。これは、コンパイル時に定数であることがわかっている式を単純化するものだ。

例えば、こんなコードを見てみる。

```cpp:func.cpp
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

```nasm:func.s
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

これは配列の長さを指定して、内積を取るプログラムを吐くスクリプトである。例えば

```sh
$ ruby dump.rb 10
```

などとすると、こんなソースを吐く。

```cpp
#include <cstdio>
const int N = 10;
const int a[] = {1,2,3,4,5,6,7,8,9,10};

int func(int b[N]) {
  int sum = 0;
  for (int i = 0; i < N; i++) {
    sum += a[i] * b[i];
  }
  return sum;
}

int main() {
  int b[] = {1,2,3,4,5,6,7,8,9,10};
  printf("%d\n", func(b));
}
```

これで、`N`をいろいろ変えてみて、どこまで即値で返せるか確認してみよう。

まず`N=5`。

```sh
$ ruby dump.rb 5 > test.cpp; g++ -O3 -S test.cpp
```

```asm
_main:
LFB2:
  subq  $8, %rsp
LCFI0:
  movl  $55, %esi
  xorl  %eax, %eax
  leaq  lC0(%rip), %rdi
  call  _printf
  xorl  %eax, %eax
  addq  $8, %rsp
LCFI1:
  ret
```

まだいけてますね。次、`N=6`。

```asm
_main:
LFB2:
  leaq  lC1(%rip), %rdi
  subq  $8, %rsp
LCFI0:
  xorl  %eax, %eax
  movdqa  lC0(%rip), %xmm2
  movdqa  __ZL1a(%rip), %xmm1
  movdqa  %xmm2, %xmm0
  psrlq $32, %xmm2
  pmuludq __ZL1a(%rip), %xmm0
  pshufd  $8, %xmm0, %xmm0
  psrlq $32, %xmm1
  pmuludq %xmm2, %xmm1
  pshufd  $8, %xmm1, %xmm1
  punpckldq %xmm1, %xmm0
  movdqa  %xmm0, %xmm1
  psrldq  $8, %xmm1
  paddd %xmm1, %xmm0
  movdqa  %xmm0, %xmm1
  psrldq  $4, %xmm1
  paddd %xmm1, %xmm0
  movd  %xmm0, %esi
  addl  $61, %esi
  call  _printf
  xorl  %eax, %eax
  addq  $8, %rsp
LCFI1:
  ret
```

あ、力尽きた。というわけでGCCはループを5倍展開はできるが、6倍展開はしない。

次、Clangでも試してみよう。GCCが諦めた`N=6`から。

```sh
$ ruby dump.rb 6 > test.cpp; clang++ -O3  -S test.cpp
```

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pushq %rbp
  .cfi_def_cfa_offset 16
  .cfi_offset %rbp, -16
  movq  %rsp, %rbp
  .cfi_def_cfa_register %rbp
  leaq  L_.str(%rip), %rdi
  movl  $91, %esi
  xorl  %eax, %eax
  callq _printf
  xorl  %eax, %eax
  popq  %rbp
  retq
```

まだいけそうですね。`N=10`は？

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pushq %rbp
  .cfi_def_cfa_offset 16
  .cfi_offset %rbp, -16
  movq  %rsp, %rbp
  .cfi_def_cfa_register %rbp
  leaq  L_.str(%rip), %rdi
  movl  $385, %esi              ## imm = 0x181
  xorl  %eax, %eax
  callq _printf
  xorl  %eax, %eax
  popq  %rbp
  retq
```

え？まだいけそう？じゃあ限界を調べてみましょう。

# clang++に定数配列を含むループ展開を食わせた場合、XX回転で力尽きる

「clang++は、定数配列を含むループ展開を何回転まで定数畳み込みをやってくれるんでしょうか？これってトリビアになりませんか？」

このトリビアの種、つまりこういうことになります。

「clang++に定数配列を含むループ展開を食わせた場合、XX回転で力尽きる」

実際に、調べてみた。

まず、`N=100`から。

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pushq %rbp
  .cfi_def_cfa_offset 16
  .cfi_offset %rbp, -16
  movq  %rsp, %rbp
  .cfi_def_cfa_register %rbp
  leaq  L_.str(%rip), %rdi
  movl  $338350, %esi           ## imm = 0x529AE
  xorl  %eax, %eax
  callq _printf
  xorl  %eax, %eax
  popq  %rbp
  retq
```

まだ大丈夫。

次、`N=200`。

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pushq %rbp
  .cfi_def_cfa_offset 16
  .cfi_offset %rbp, -16
  movq  %rsp, %rbp
  .cfi_def_cfa_register %rbp
  leaq  L_.str(%rip), %rdi
  movl  $2686700, %esi          ## imm = 0x28FEEC
  xorl  %eax, %eax
  callq _printf
  xorl  %eax, %eax
  popq  %rbp
  retq
```

まだできている。

`N=300`を食わせる。

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pxor  %xmm0, %xmm0
  movl  $12, %eax
  leaq  l___const.main.b(%rip), %rcx
  pxor  %xmm1, %xmm1
  jmp LBB1_1
  .p2align  4, 0x90
LBB1_3:                                 ##   in Loop: Header=BB1_1 Depth=1
  movdqa  -16(%rcx,%rax,4), %xmm0
  movdqa  (%rcx,%rax,4), %xmm1
  pmulld  %xmm0, %xmm0
  pmulld  %xmm1, %xmm1
  paddd %xmm3, %xmm0
  paddd %xmm2, %xmm1
  addq  $16, %rax
LBB1_1:                                 ## =>This Inner Loop Header: Depth=1
  movdqa  -48(%rcx,%rax,4), %xmm3
  movdqa  -32(%rcx,%rax,4), %xmm2
  pmulld  %xmm3, %xmm3
  paddd %xmm0, %xmm3
  pmulld  %xmm2, %xmm2
  paddd %xmm1, %xmm2
  cmpq  $300, %rax              ## imm = 0x12C
  jne LBB1_3
(snip)
```

力尽きた。その限界を二分法で調べよう。`N=223`。

```sh
$ ruby dump.rb 223 > test.cpp; clang++ -O3  -S test.cpp
```

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pushq %rbp
  .cfi_def_cfa_offset 16
  .cfi_offset %rbp, -16
  movq  %rsp, %rbp
  .cfi_def_cfa_register %rbp
  leaq  L_.str(%rip), %rdi
  movl  $3721424, %esi          ## imm = 0x38C8D0
  xorl  %eax, %eax
  callq _printf
  xorl  %eax, %eax
  popq  %rbp
  retq
```

即値を返している。

`N=224`。

```sh
$ ruby dump.rb 224 > test.cpp; clang++ -O3  -S test.cpp
```

```nasm
_main:                                  ## @main
  .cfi_startproc
## %bb.0:
  pxor  %xmm0, %xmm0
  movl  $12, %eax
  leaq  l___const.main.b(%rip), %rcx
  pxor  %xmm1, %xmm1
  .p2align  4, 0x90
LBB1_1:                                 ## =>This Inner Loop Header: Depth=1
  movdqa  -48(%rcx,%rax,4), %xmm2
  movdqa  -32(%rcx,%rax,4), %xmm3
  pmulld  %xmm2, %xmm2
  paddd %xmm0, %xmm2
  movdqa  -16(%rcx,%rax,4), %xmm0
  pmulld  %xmm3, %xmm3
  paddd %xmm1, %xmm3
  movdqa  (%rcx,%rax,4), %xmm1
  pmulld  %xmm0, %xmm0
  paddd %xmm2, %xmm0
  pmulld  %xmm1, %xmm1
  paddd %xmm3, %xmm1
  addq  $16, %rax
  cmpq  $236, %rax
  jne LBB1_1
```

力尽きた。

# まとめ

こうしてこの世界にまた一つ
新たなトリビアが生まれた。

clang++は、定数関数を含むループの定数畳み込みを、224回転で力尽きる。

# 他のコンパイラいじめ関連記事

* [C++でアスタリスクをつけすぎると端末が落ちる](https://qiita.com/kaityo256/items/d54439246edc1cc58121)
* [コンパイラは関数のインライン展開を☓☓段で力尽きる](https://qiita.com/kaityo256/items/b4dc66c92338c0b92552)
* [関数ポインタと関数オブジェクトのインライン展開](https://qiita.com/kaityo256/items/5911d50c274465e19cf6)
* [インテルコンパイラのアセンブル時最適化](https://qiita.com/kaityo256/items/e7b05eb9c2bfbbd434a7)
* [GCCの最適化がインテルコンパイラより賢くて驚いた話](https://qiita.com/kaityo256/items/72c1bf93a210e450308c)