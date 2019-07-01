
# はじめに

多くの言語にはスコープの概念がある。そして、スコープにより「スコープの外側」「内側」という概念が生まれる。この時、スコープの外側の変数名を内側からどのように参照すべきかが問題となる。この変数の名前解決については、だいぶわかったつもりでいたんだけど、全然わかってなかったので、ここにまとめておく。以下、いくつかの言語の比較をするが、どの言語が良いとか悪いとか言うつもりは全くない。ただ「言語ごとに結構ポリシーが違う」ということを共有したくてこの記事を書いた。

# 経緯

いま、[Pythonの講義ノート](https://github.com/kaityo256/python_zero)を書いているのだが、そのスコープのところでこんなことを書いた。

<blockquote class="twitter-tweet" data-lang="ja"><p lang="ja" dir="ltr">まぁこんな話です。 <a href="https://t.co/wvG9unkkzI">pic.twitter.com/wvG9unkkzI</a></p>&mdash; ロボ太 (@kaityo256) <a href="https://twitter.com/kaityo256/status/1140564261640343553?ref_src=twsrc%5Etfw">2019年6月17日</a></blockquote>

これは、ローカル変数によるグローバル変数の上書きの例として出したもので、こんなコードだ。

```py
a = 10
def func():
    print(a)
    a = 20
```

すると、こういう指摘をいただいた。

<blockquote class="twitter-tweet" data-lang="ja"><p lang="ja" dir="ltr">右の例はfuncの中のprintで代入前参照のエラー出ませんか？</p>&mdash; 片山 功士 (@katayama_k) <a href="https://twitter.com/katayama_k/status/1140955575578058753?ref_src=twsrc%5Etfw">2019年6月18日</a></blockquote>

この指摘は正しく、先程のコードはエラーになる。つまり、

```py
a = 10
def func():
    print(a)
```

このコードはグローバル変数`a`を表示する。

```py
a = 10
def func():
    a = 20
```

このコードはローカル変数`a`を宣言する。

そして、

```py
a = 10
def func():
    print(a)
    a = 20
```

このコードは、関数`func`内に`a`への代入文があるので`a`はローカル変数とみなされ、`print`文実行時には未定義なのでエラーとなる。

どうしてこうなるかは、西尾さんの指摘

<blockquote class="twitter-tweet" data-lang="ja"><p lang="ja" dir="ltr">関数の中である名前への代入があると、その名前はその関数のローカル変数だと判定され、異なるバイトコードへとコンパイルされるのです。</p>&mdash; nishio hirokazu (@nishio) <a href="https://twitter.com/nishio/status/1140999930628042752?ref_src=twsrc%5Etfw">2019年6月18日</a></blockquote>

や、[スクラップボックスの記事](https://scrapbox.io/nishio/Python%E3%81%AE%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E5%A4%89%E6%95%B0)の通り。

で、このあたりの名前解決の話をつらつら書こうかな、と思う。

# グローバル変数とローカル変数

先のPythonのコード、

```py
a = 10
def func():
    print(a)
    a = 20
```

は、`print`文ではグローバル変数を参照し、代入文ではローカル変数の宣言となることを意図して書いたものだが、前述の通りエラーとなる。C++で同じことをするとこんな感じになるだろう。

```cpp
#include <iostream>

int a = 10;

void func(){
  std::cout << a << std::endl; //グローバル変数が参照される
  int a = 20; //ローカル変数が宣言される
}

int main(){
  func();
  std::cout << a << std::endl; // グローバル変数は影響を受けない
}
```

これは意図どおり、最初の表示はグローバル変数を参照し、次の代入文では`a`はローカル変数として扱われる。C++は「変数の宣言」と「代入」が別れている言語だ。したがって、`int a`とある時点で変数宣言であるとわかる。

しかしPythonは変数宣言を代入によって行う。したがって、

```py
a = 20
```

とある時に、これが変数宣言となるか、別の場所で宣言された変数への代入になるかは文脈によって決まる。

```py
a = 10
def func():
    a = 20
```

などとすると、Pythonでは`a = 20`はローカル変数の宣言とみなされ、グローバル変数は影響を受けない。

C++はローカルスコープ内からグローバル変数を触ることができる。

```cpp
#include <iostream>

int a = 10;

void func(){
  a = 20; // グローバル変数の書き換え
}

int main(){
  func();
  std::cout << a << std::endl; // func内で書き換えられた値が表示される
}
```

Pythonで同様なことをするには、`global`宣言により、変数`a`がグローバル変数であることを明示する必要がある。

```py
a = 10
def func():
    global a
    a = 20 # グローバル変数`a`の値が書き換えられる。
```

さて、RubyもPythonのように代入により変数の宣言を行う言語だが、グローバル変数は`$`をつけるという文法だ。したがって、Pythonのように「ローカル変数なのか、グローバル変数なのか」という問題はおきない。

```rb
$a = 10
def func
    $a = 20
end
```

まとめるとこんな感じ。グローバルとローカルに同じ名前の変数がある場合、

* Rubyはグローバル変数に`$`をつけるので、ローカルとグローバルの変数名がぶつからない。
* Pythonは、ローカルスコープからグローバル変数を参照できる。しかし、代入文があると、そのスコープ全体にわたってローカル変数であるとみなされる。
* C++は宣言と代入が別れているので、ローカル変数宣言があるまではグローバル変数と、宣言があった後はローカル変数とみなされる。

# ネストするスコープ

## Pythonの場合

Pythonは、関数の中の関数、「関数内関数」を作ることができる。この時、関数のスコープがネストするので、先程「グローバル変数」「ローカル変数」で起きたことと同じことが「外側の関数の変数」「内側の関数の変数」でおきる。

```py:nest1.py
def func1():
    a = 10
    def func2():
        a = 20
    print(a)

func1() #=> 10
```

外側の関数でローカル変数`a`が定義されており、それは内側の関数`func2`から参照できる。また、`func2`内で変数を書き換えても、外側に影響を与えない。

```py:nest2.py
def func1():
    a = 10
    def func2():
        a = 20
    print(a)

func1() #=> 10
```

## Ruby

Rubyはどうだろう？以下、

Rubyもメソッド内メソッドを作ることはできるが、**スコープはネストしない**。例えばこんなコードを書いてみる。

```rb:nest1.rb
def func1
  a = 10
  def func2
    puts a
  end
  func2
end

func1
```

Python同様に、内側のメソッド`func2`から、外側のメソッド`func1`のローカル変数を参照することを意図したコードだが、これはエラーとなる。Rubyのメソッド内メソッドはスコープをネストさせず、上記のコードは以下と等価だ。

```rb:nest2.rb
def func1
  a = 10
  func2
end

def func2
  puts a
end

func1
```

`func1`と`func2`は同じスコープに所属し、それぞれ独立したスコープを持つ(親子関係がない)。したがって、`func2`から`func1`のローカル変数`a`を参照しようとしても「知らないよ」となる。

Rubyにおいてメソッド内メソッドとは、「外側のメソッドが実行された時に内側のメソッドが定義される」という動作をするものだ。したがって、メソッド内メソッドを、メソッドの外側から呼ぶことができる。

```rb:nest3.rb
def func1
  def func2
    puts "Hello func2"
  end
end

func1
func2
```

これを見ても、`func1`と`func2`が同じスコープに所属していることがわかると思う。Pythonで同じことをするとエラーになる。

```py:nest3.py
def func1():
    def func2():
        print("Hello func2")

func1()
func2()
```

## C++

C++ではどうだろうか？C++においては、関数オブジェクトを使えば関数内関数と似たようなことが実現できる。

```cpp:nest1.cpp
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
  func1();　// => "Hello func2"
}
```

これは`func1`内に定義された関数オブジェクト`func2`を実行している。もちろん`func2`は`func1`のスコープ内にあり、外からは見ることができない。

さて、内側の関数`func2`から外側のローカル変数を触れるだろうか？やってみよう。

```cpp:nest2.cpp
#include <iostream>

void func1(){
  int a = 10;
  struct {
    void operator()(){
      a = 20;
    }
  }func2;
  func2();
  std::cout << a << std::endl;
}

int main(){
  func1();
}
```

これは`func1`のローカル変数`a`を`func2`から触りに行こうとしたものだが、コンパイル時にこんなことを言われて怒られる。

```sh
$ g++ nest2.cpp
nest2.cpp: In member function 'void func1()::<unnamed struct>::operator()()':
nest2.cpp:7:7: error: use of local variable with automatic storage from containing function
    7 |       a = 20;
      |       ^
nest2.cpp:4:7: note: 'int a' declared here
    4 |   int a = 10;
      |       ^

```

エラーメッセージをよく読むと「内側の関数からautomatic storageのローカル変数を触ろうとしているよ」と言われているので、外側の変数に`static`をつけてみよう。

```cpp:nest3.cpp
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
```

```sh
$ g++ nest3.cpp
$ ./a.out
20
```

問題なく実行できた。`static`をつけなかった場合に怒られたのは、内側から外側の変数を触りにいこうとした時に、その変数のアドレスが決まらないためだ。`static`をつければ変数のアドレスが決まるので内側から表示することも修正することもできる。

## Java

Javaはどうだろうか。とりあえず関数内にクラスを作り、関数内で宣言された変数を参照してみよう。

```java:nest1.java
class nest1 {
  
  void func1(){
    int a = 10;
    class inner{
      void func2(){
        System.out.println(a);
      }
    }
    (new inner()).func2();
  }

  public static void main(String[] args){
    (new nest1()).func1();
  }
}

```

`func1`内に定義されたローカル変数`a`を、`func1`内に定義された`inner`クラスのメソッド`func2`から参照している。このコードは問題なく実行できる。

```sh
$ javac nest1.java
$ java nest1
10
```

次に、内側からローカル変数の値を修正してみよう。

```java:nest2.java
class nest2 {

  void func1(){
    int a = 10;
    class inner{
      void func2(){
        a = 20;
      }
    }
    (new inner()).func2();
  }

  public static void main(String[] args){
    (new nest2()).func1();
  }
}
```

これはコンパイル時に怒られる。

```sh
$ javac nest2.java
nest2.java:7: エラー: 内部クラスから参照されるローカル変数は、finalまたは事実上のfinalである必要があります
        a = 20;
        ^
エラー1個
```

実は、内部クラスから外側のローカル変数を触る場合、その変数は`final`、もしくはエラーメッセージにあるように、「事実上のfinal (effectively final)」である必要がある。Javaは、内部クラスから外側のローカル変数を触りにいく時、もしその変数が`final`宣言されていなくても、それを`final`とみなす。したがって、「外側のローカル変数は参照はできるが、変更は許さない」というポリシーだ。

## ネストするスコープのまとめ

まとめるとこんな感じ。

* Pythonの関数内関数はスコープをネストさせ、グローバル変数とローカル変数の場合と同じような名前解決をする。
* C++はスコープをネストさせ、外側のローカル変数がstaticなら内側から参照、値の代入ができる。
* Javaはスコープをネストさせ、内側から外側のローカル変数の参照は許すが代入は許さない(final指定を要求する)
* Rubyはスコープをネストさせない

# 宣言時に存在しない変数の扱い

名前解決といえば、関数宣言時に存在しない名前をどうするか、という問題がある。例えばPythonでこんな関数を定義する。

```py
def func():
    print(a)
```

この関数を定義した時には変数`a`は宣言されていない。しかし、この関数定義はエラーにならない。実行前に`a`が宣言されるかもしれないからだ。

```py
def func():
    print(a)

a = 10 # ここでaを宣言する
func() #=> 10
```

もちろん、実行時までに宣言されていなければエラーになる。

```py
def func():
    print(a)

func() #=> NameError: name 'a' is not defined
```

つまり、Pythonでは関数宣言時は、グローバル変数と思しき変数については名前解決を棚上げしなくてはならない。

ちなみに、Rubyでは宣言されていないグローバル変数表示しようとしてもエラーにはならず、変数は`nil`となる。

```rb
def func
    puts $a
end

func #=> nil
```

さて、C++においては、関数宣言時に必要な名前が全て宣言されていなければならない。つまり、以下のようなコードはエラーになる。

```cpp

