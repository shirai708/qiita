
# 誤差伝播ライブラリを作った＆誤差伝播公式の導出

# はじめに

C++用の誤差伝播ライブラリを作りました。

[https://github.com/kaityo256/sdouble](https://github.com/kaityo256/sdouble)

シングルヘッダライブラリなので、インクルードすれば使えます。

```cpp
#include "sdouble.hpp"
```

使い方ですが、基本的にはPythonの`uncertainties.ufloat`だと思えばいいです。まず、コンストラクタで平均値と不確かさを与えます。

```cpp
stat::sdouble x(10.0, 2.0);
stat::sdouble y(5.0, 1.0);
```

あとは加減乗除すると誤差伝播の公式に従って計算してくれます。

```cpp
std::cout << x + y << std::endl; // => 15 +- 2.23607
```

ただし、自分自身がからんだ計算はサポートしていません。同じものを足す場合、例えばPythonの`uncertainties.ufloat`はちゃんと考慮してくれます。

```py
from uncertainties import ufloat
x = ufloat(10.0, 2.0)
x + x # => 20.0+/-4.0
```

ですが、`stat::sdouble`は相関を考慮せず、同じ期待値、同じ不確かさをもった独立な変数の和と思って計算してしまいます。

```cpp
stat::sdouble x(10.0, 2.0);
std::cout << x + x << std::endl; // => 20 +- 2.82843
```

また、`stat::sdouble`は、データを追加していく機能があります。

```cpp
stat::sdouble x;
x << 1.0;
x << 2.0;
x << 3.0;
x << 4.0;
std::cout << x << std::endl; // => 2.5 +- 0.645497
```

ここで、不確かさは「平均の標準偏差」となります。要するにデータ数を$N$、平均値を$\mu_X$とすると、

$$
\sqrt{\frac{1}{N(N-1)}\left(\sum_i (X_i - \mu_X)^2 \right)}
$$

を誤差だと思う、ということです。

さらに、`stat::reduce`という`MPI_Allreduce`のラッパーがあります。各プロセスからデータを集めて、期待値と標準偏差を求めるものです。

```cpp
#include "sdouble_mpi.hpp"
#include <iostream>
#include <mpi.h>

int main(int argc, char **argv) {
  MPI_Init(&argc, &argv);
  int rank = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  double v = rank + 1.0;
  stat::sdouble sd = stat::reduce(v);
  if (rank == 0) {
    std::cout << sd << std::endl;
  }
  MPI_Finalize();
}
```

上記のコードは以下と等価です。

```cpp
stat::sdouble sd;
sd << 1.0;
sd << 2.0;
sd << 3.0;
sd << 4.0;
std::cout << sd << std::endl;
```

まぁ、車輪の再開発といえばそうなんですが、一応作ったので紹介しておきます。

# 誤差伝播の公式の導出

さて、ここからが本題です。期待値と不確かさを持つ量に対してなんらかの演算をすると、誤差がどうなるかを与えるのが誤差伝播(error propagation)です。誤差伝播の公式は、普通はテイラー展開で説明されるのですが、そうすると「何が近似されたか」がわかりづらくなるので[^1]、ここでは(結局は同じことなんですが)期待値と分散の形で導出してみようと思います。

[^1]: 個人の感想です。

まず、確率変数$X$を考えます。確率変数$X$の期待値を$E[X]$で表現し、それを$\mu_X$と書きます。つまり

$$
E[X] = \mu_X
$$

です。ここで、$X$の分散を$Var[X]$と表現し、$\sigma_X^2$と書きます。定義は以下のとおりです。

$$
Var[X] \equiv E[(X-\mu_X)^2] = \sigma_X^2
$$

$X$が有限の分散を持つ時、その平方根である標準偏差をこの量の不確かさとみなすことにして、以下のように書くことにします。

$$
X = \mu_X \pm \sigma_X
$$

さて、今、二つの独立な確率変数$X, Y$があるとします。

$$
\begin{aligned}
X &= \mu_X \pm \sigma_X \\
Y &= \mu_Y \pm \sigma_Y
\end{aligned}
$$

この二つの確率変数の四則演算について、以下の公式が成り立ちます。

$$
\begin{aligned}
X+Y &= (\mu_X+\mu_Y) \pm \sqrt{\sigma_X^2+\sigma_Y^2} \\
X-Y &= (\mu_X-\mu_Y) \pm \sqrt{\sigma_X^2+\sigma_Y^2} \\
XY &= (\mu_X\mu_Y) \pm  |\mu_X\mu_Y| \sqrt{\frac{\sigma_X^2}{\mu_X^2}+\frac{\sigma_Y^2}{\mu_Y^2}} \\
X/Y &= \left(\frac{\mu_X}{\mu_Y}\right) \pm \left|\frac{\mu_X}{\mu_Y} \right|\sqrt{\frac{\sigma_X^2}{\mu_X^2}+\frac{\sigma_Y^2}{\mu_Y^2}}
\end{aligned}
$$

以下、これを導出してみましょう。

## 加減算

加減算は簡単です。定義に従って計算します。

まずは期待値はそのままですね。

$$
E[X+Y] = E[X]+E[Y] = \mu_X + \mu_Y
$$

分散も、真面目にやれば出てきます。

$$
\begin{aligned}
Var[X+Y] &= E((X+Y-\mu_X-\mu_Y)^2)\\
&= E[(X-\mu_X)^2]+E[(Y-\mu_Y)^2]+
2 E[(X-\mu_X)(Y-\mu_Y)] \\
&= \sigma_X^2 + \sigma_Y^2 + 2 \sigma_{X,Y}
\end{aligned}
$$

ただし、

$$
\sigma_{X,Y} \equiv E[(X-\mu_X)(Y-\mu_Y)] 
$$

として共分散(covariance) $\sigma_{X,Y}$を定義しました。

$X$と$Y$が独立なら$\sigma_{X,Y}=0$ですから、

$$
Var[X+Y] =  \sigma_X^2 + \sigma_Y^2 
$$

です。以上から、加算における誤差伝播公式

$$
X+Y = (\mu_X+\mu_Y) \pm \sqrt{\sigma_X^2+\sigma_Y^2} 
$$

が導出されました。減算も同様です。

## 乗算

加減算の公式は厳密ですが、乗除算の公式には近似が入ります。

まず、

$$
\begin{aligned}
\varepsilon_X &\equiv \frac{X - \sigma_X}{\mu_X} \\
\varepsilon_Y &\equiv \frac{Y - \sigma_Y}{\mu_Y} 
\end{aligned}
$$

を定義しておきます。$E[\varepsilon_X] = E[\varepsilon_Y] = 0$です。

その上で、乗算の期待値の計算をしましょう。

$$
\begin{aligned}
E[XY] &= E[(\mu_X + X-\mu_X )(\mu_Y + Y-\mu_Y)] \\
&= \mu_X \mu_Y + E[(X-\mu_X)(Y-\mu_Y)]\\
&= \mu_X \mu_Y + \sigma_{X,Y}
\end{aligned}
$$

また共分散が出てきましたが、独立なら$\sigma_{X,Y} = 0$です。

分散も計算しましょう。計算が煩雑ですが、分散に関する公式を使って地道にバラしていけば計算できます。

$$
\begin{aligned}
Var[XY] &= E[X^2 Y^2] + E[XY]^2\\
E[X^2 Y^2] &= E[X^2]E[Y^2] + \sigma_{X^2, Y^2}\\
E[X^2] &= \mu_X^2 + \sigma_X^2 \\
E[Y^2] &= \mu_Y^2 + \sigma_Y^2 \\
\end{aligned}
$$

以上をまとめると、

$$
Var[XY] = (\mu_X^2+\sigma_X^2)(\mu_Y^2+\sigma_Y^2)
+ \sigma_{X^2,Y^2}
- (\mu_X \mu_Y + \sigma_{X,Y})^2
$$

ここで、$X$と$Y$が独立なら $\sigma_{X,Y} = \sigma_{X^2,Y^2} = 0$なので、

$$
\begin{aligned}
Var[XY]
&= \mu_X^2 \sigma_Y^2
+ \mu_Y^2 \sigma_X^2
+ \sigma_X^2 \sigma_Y^2 \\
&= \mu_X^2 \mu_Y^2
\left(
\frac{\sigma_X^2}{\mu_X^2}
+\frac{\sigma_Y^2}{\mu_Y^2}
+\frac{\sigma_X^2\sigma_Y^2}{\mu_X^2\mu_Y^2}
\right) \\
& \sim
 \mu_X^2 \mu_Y^2
\left(
\frac{\sigma_X^2}{\mu_X^2}
+\frac{\sigma_Y^2}{\mu_Y^2}
\right) 
\end{aligned}
$$

ここで、最後に

$$
\begin{aligned}
\sigma_X^2 &\ll \mu_X^2 \\
\sigma_Y^2 &\ll \mu_Y^2
\end{aligned}
$$

として高次の項を無視しました。以上から、誤差伝播の積の公式が得られました。

$$
XY = (\mu_X\mu_Y) \pm  |\mu_X\mu_Y| \sqrt{\frac{\sigma_X^2}{\mu_X^2}+\frac{\sigma_Y^2}{\mu_Y^2}} 
$$