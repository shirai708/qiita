
# printfに4285個アスタリスクをつけるとclang++が死ぬ

## はじめに

こんな記事を読みました。

[C で関数に * や & を付けられる件の説明: ***printf の謎](https://qiita.com/lo48576/items/92f1fc90643373d0b167)

なんと、`printf`を`(***printf)`などとしても普通に呼べるのだそうです。それじゃ、アスタリスク100個とかつけても大丈夫なのでしょうか。

```cpp:test.cpp
#include <cstdio>
int main(){
  (****************************************************************************************************printf)("Hello World\n");
}
```

```sh
$ clang++ test.cpp
$ ./a.out
Hello World
```

大丈夫そうですね。

では、もっとつけたらどうでしょう？1万個つけたら？

```rb:check.rb
def check(n)
  s = "*"*n
  f = open("test.cpp","w")
  f.puts <<EOS
#include <cstdio>
int main(){
(#{s}printf)("Hello World\\n");
}
EOS
  f.close()
  return system("clang++ test.cpp")
end

check(ARGV[0].to_i)
```

```sh
$ ruby check.rb 10000
clang: error: unable to execute command: Illegal instruction: 4
clang: error: clang frontend command failed due to signal (use -v to see invocation)
Apple LLVM version 10.0.1 (clang-1001.0.46.4)
Target: x86_64-apple-darwin18.7.0
Thread model: posix
InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
clang: note: diagnostic msg: PLEASE submit a bug report to http://developer.apple.com/bugreporter/ and include the crash backtrace, preprocessed source, and associated run script.
clang: note: diagnostic msg:
********************

PLEASE ATTACH THE FOLLOWING FILES TO THE BUG REPORT:
Preprocessed source(s) and associated run script(s) are located at:
clang: note: diagnostic msg: /var/folders/5x/jy4d20b97jgcsgf4mt7dwwqr0000gn/T/test-080e88.cpp
clang: note: diagnostic msg: /var/folders/5x/jy4d20b97jgcsgf4mt7dwwqr0000gn/T/test-080e88.sh
clang: note: diagnostic msg: /var/folders/5x/jy4d20b97jgcsgf4mt7dwwqr0000gn/T/test-080e88.crash
clang: note: diagnostic msg:

********************
```

**clang++がSIGILLで死にました**ね。というわけでどのあたりで死ぬか、確認してみましょう。

ちなみに試した環境はこんな感じ。

* macOS X 10.14.6 (Mojave)
  * Apple LLVM version 10.0.1 (clang-1001.0.46.4)
* Red Hat Enterprise Linux Server release 7.4 (Maipo)
  * icpc (ICC) 18.0.5 20180823
  * g++ (GCC) 7.2.0

## printfにXX個アスタリスクをつけるとclang++が死ぬ

「clang++は、printfにいくつまでアスタリスクをつけられるんでしょうか？これってトリビアになりませんか？」

このトリビアの種、つまりこういうことになります。

「printfにXX個アスタリスクをつけるとclang++が死ぬ」

実際に、調べてみた。

つってもRubyで手抜き二分探索書くだけ。

```rb:search.rb
def check(n)
  s = "*"*n
  f = open("test.cpp","w")
  f.puts <<EOS
#include <cstdio>
int main(){
(#{s}printf)("Hello World\\n");
}
EOS
  f.close()
  return system("clang++ test.cpp 2> /dev/null")
end

def binary_search
  s = 1
  e = 10000
  while s!=e and s+1!=e
    m = (s+e)/2
    if check(m)
      puts "#{m} OK"
      s = m
    else
      puts "#{m} NG"
      e = m
    end
  end
end

binary_search
```

```sh
$ ruby search.rb
5000 NG
2500 OK
3750 OK
4375 NG
4062 OK
4218 OK
4296 NG
4257 OK
4276 OK
4286 NG
4281 OK
4283 OK
4284 OK
4285 NG
```

4284個はOK、4285個は死にました。

## icpc

インテルコンパイラも調べてみましょう。スクリプトの`clang++`を`icpc`に変えて実行します。

```sh
$ ruby search.rb
5000 NG
2500 NG
1250 OK
1875 OK
2187 OK
2343 NG
2265 NG
2226 OK
2245 OK
2255 OK
2260 OK
2262 OK
2263 OK
2264 NG
```

2264個で力尽きるみたいですね。ただ、他のバージョンでは実行するたびに微妙に死ぬサイズが変わるので、メモリがらみなのかもしれません。

## GCC

g++も調べてみましょう。

```sh
$ ruby search.rb
5000 OK
7500 OK
8750 OK
9375 OK
9687 OK
9843 OK
9921 OK
9960 OK
9980 OK
9990 OK
9995 OK
9997 OK
9998 OK
9999 OK
```

おや？g++は1万個のアスタリスクをものともしません。5万個は？

```sh
$ ruby search.rb
25000 OK
37500 OK
43750 OK
46875 OK
48437 OK
49218 OK
49609 OK
49804 OK
49902 OK
49951 OK
49975 OK
49987 OK
49993 OK
49996 OK
49998 OK
49999 OK
```

問題ないようです。

それじゃ一気に100万個！

```sh
$ ruby search.rb
500000 OK
750000 OK
875000 OK
937500 OK
968750 OK
984375 OK
992187 OK
996093 OK
998046 OK
999023 OK
999511 OK
999755 OK
999877 OK
999938 OK
999969 OK
999984 OK
999992 OK
999996 OK
999998 OK
999999 OK
```

別の場所で試したら75000あたりで**コア吐いた**ので、おそらくメモリが許す限りいくらでもいけるっぽいです。

## まとめ

こうしてこの世界にまた一つ
新たなトリビアが生まれた。

printfに4285個アスタリスクをつけるとclang++が死ぬ

printfに2264個くらいアスタリスクをつけるとインテルコンパイラも死ぬ

g++は(メモリの許す限り)アスタリスクをつけることができる。とりあえず100万個まで確認。

というわけで、みなさんがもし「ああ！関数呼び出しに心ゆくまで思いっきりアスタリスクつけたい！」と思ったら、GCCを使うのがよいと思います。

## これまでのコンパイラいじめの記録

* [定数配列がからんだ定数畳み込み最適化](https://qiita.com/kaityo256/items/bf9712559c9cd2ce4e2c)
* [C++でアスタリスクをつけすぎると端末が落ちる](https://qiita.com/kaityo256/items/d54439246edc1cc58121)
* [整数を419378回インクリメントするとMacのg++が死ぬ](https://qiita.com/kaityo256/items/6b5715b213e955d44f55)
* [コンパイラは関数のインライン展開を☓☓段で力尽きる](https://qiita.com/kaityo256/items/b4dc66c92338c0b92552)
* [関数ポインタと関数オブジェクトのインライン展開](https://qiita.com/kaityo256/items/5911d50c274465e19cf6)
* [インテルコンパイラのアセンブル時最適化](https://qiita.com/kaityo256/items/e7b05eb9c2bfbbd434a7)
* [GCCの最適化がインテルコンパイラより賢くて驚いた話](https://qiita.com/kaityo256/items/72c1bf93a210e450308c)

## 2019年8月22日追記

Twitterで原因を調べてくださった方がいたので、僕も少し調べてみました。

<blockquote class="twitter-tweet"><p lang="ja" dir="ltr">****printf()のやつ完全に理解した。同じ現象を引き起こすコードかけました<br>int main(){<br>int i=0;<br>i++,i++,i++,i++,i++, <br><br>以下6000個近くです<a href="https://t.co/8qng7Zw0eq">https://t.co/8qng7Zw0eq</a></p>&mdash; 道路 (@Nperair) <a href="https://twitter.com/Nperair/status/1164190979991019520?ref_src=twsrc%5Etfw">August 21, 2019</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

<blockquote class="twitter-tweet"><p lang="ja" dir="ltr">たぶん短絡評価不能な式を沢山ぶちこむと死ぬという話だった</p>&mdash; 道路 (@Nperair) <a href="https://twitter.com/Nperair/status/1164194274935627776?ref_src=twsrc%5Etfw">August 21, 2019</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

<blockquote class="twitter-tweet"><p lang="ja" dir="ltr"><a href="https://t.co/nIpVbZ2hq2">https://t.co/nIpVbZ2hq2</a><br>1037行目からです</p>&mdash; 道路 (@Nperair) <a href="https://twitter.com/Nperair/status/1164194472357318656?ref_src=twsrc%5Etfw">August 21, 2019</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

この方の調査では`i++,`を重ねたために`Address CodeGenFunction::EmitPointerWithAlignment`で死んでいるようですが、本稿の`printf`にアスタリスクをたくさんつける場合は`Parser::ParseCastExpression`で死ぬみたいですね。

```sh
(gdb) r -cc1 -triple x86_64-redhat-linux-gnu -emit-obj -mrelax-all -disable-free -disable-llvm-verifier -main-file-name test.cpp -mrelocation-model static -mdisable-fp-elim -fmath-errno -masm-verbose -mconstructor-aliases -munwind-tables -fuse-init-array -target-cpu x86-64 -target-linker-version 2.27 -fdeprecated-macro -ferror-limit 19 -fmessage-length 80 -mstackrealign -fobjc-runtime=gcc -fcxx-exceptions -fexceptions -fdiagnostics-show-option -fcolor-diagnostics -vectorize-slp -x c++ test-75d014.cpp
Starting program: /usr/bin/clang -cc1 -triple x86_64-redhat-linux-gnu -emit-obj -mrelax-all -disable-free -disable-llvm-verifier -main-file-name test.cpp -mrelocation-model static -mdisable-fp-elim -fmath-errno -masm-verbose -mconstructor-aliases -munwind-tables -fuse-init-array -target-cpu x86-64 -target-linker-version 2.27 -fdeprecated-macro -ferror-limit 19 -fmessage-length 80 -mstackrealign -fobjc-runtime=gcc -fcxx-exceptions -fexceptions -fdiagnostics-show-option -fcolor-diagnostics -vectorize-slp -x c++ test-75d014.cpp
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib64/libthread_db.so.1".

Program received signal SIGSEGV, Segmentation fault.
0x00000000009a8f60 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
```

この関数は[lib/Parse/ParseExpr.cpp](https://clang.llvm.org/doxygen/ParseExpr_8cpp_source.html)の530行目で定義されています。バックトレースをとってみましょう。

```gdb
(gdb) bt
#0  0x00000000009a8f60 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
#1  0x00000000009ab7bd in clang::Parser::ParseCastExpression(bool, bool, clang::Parser::TypeCastState) ()
#2  0x00000000009a9413 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
#3  0x00000000009ab7bd in clang::Parser::ParseCastExpression(bool, bool, clang::Parser::TypeCastState) ()
#4  0x00000000009a9413 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
#5  0x00000000009ab7bd in clang::Parser::ParseCastExpression(bool, bool, clang::Parser::TypeCastState) ()
#6  0x00000000009a9413 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
#7  0x00000000009ab7bd in clang::Parser::ParseCastExpression(bool, bool, clang::Parser::TypeCastState) ()
#8  0x00000000009a9413 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
#9  0x00000000009ab7bd in clang::Parser::ParseCastExpression(bool, bool, clang::Parser::TypeCastState) ()
#10 0x00000000009a9413 in clang::Parser::ParseCastExpression(bool, bool, bool&, clang::Parser::TypeCastState) ()
...
```

要するにParseCastExpressionを再帰的に呼び出し過ぎて、スタックが枯渇して死んだ、ということのようです。GCCは調べていませんが、おそらく再帰でパースしておらず、スタックではなくメモリが上限になる、ということのようです。インテルコンパイラは知らん。

ちなみにこれはCentOSで調べました。MacではSIGILLが出て不思議なのですが、そもそもMacのシグナルはなんか微妙だし、SIPのせいでデフォルトではデバッガが使えず、それをオフにして再起動するほどの気力もないので調べていません。ムネンアトヲタノム。
