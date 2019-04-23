
# CentOS 7にDockerでWordPressを入れる

# はじめに

CentOSでDockerを使ってWordPressを立ち上げたい、という人はわりといると思うし、記事もすでにたくさんある。
しかし、僕が必要な情報が一箇所に集まっていないのと、失敗したときに「どこまでうまくいっているのか」「どこでこけているのか」がわかりにくくて
苦労した。というわけで、ステップごとにうまくいっているか確認しながら作業を進める。
なお、セキュリティ対策についてはこの記事に含めないので各自で適切に設定されたい。

# CentOS7 インストール直後

CentOS 7をインストール直後、yum updateが終わり、一般アカウントを作ってsudoersに登録し、
そのアカウントになった。以後、その一般アカウントから操作しているものとする。

まずはファイアーウォールの80番と443番を開ける。

```sh
sudo firewall-cmd --add-service=http --zone=public --permanent
sudo firewall-cmd --add-service=https --zone=public --permanent
```

Dockerをインストールする。

```sh
sudo yum install docker
```

ここで、Dockerを実行してみると、Docker daemonに接続できない、と言われる。

```sh
$ docker ps
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

Docker daemonを実行する。

```sh
sudo systemctl start docker
```

もう一度`docker ps`を実行してみると、エラーメッセージが変わる。

```sh
$ docker ps
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get http://%2Fvar%2Frun%2Fdocker.sock/v1.26/containers/json: dial unix /var/run/docker.sock: connect: permission denied
```

これはDockerの実行にroot権限かdockerグループに所属していることが求められるため。
ユーザをdockerグループに所属させてしまえば実行できるが、セキュリティ上の問題があるため、dockerグループにパスワードを設定し、newgrpで一時的に
dockerグループに所属することで実行する。

```sh
sudo groupadd docker # dockerグループを作成
sudo gpasswd docker # ここでグループパスワードを設定
sudo systemctl restart docker # dockerをリスタート
```

この状態で、`newgrp docker`するとdockerをいじれるようになる。

```sh
$ newgrp docker # パスワードを入力して一時的にdockerグループに
$ docker ps # dockerコマンドが実行できる
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
$ exit # dockerグループを抜ける
$ docker ps # グループを抜けると実行できない
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get http://%2Fvar%2Frun%2Fdocker.sock/v1.26/containers/json: dial unix /var/run/docker.sock: connect: permission denied
```


# 参考

* [Dockerを一般ユーザで実行する](https://qiita.com/naomichi-y/items/93819573a5a51ae8cc07)