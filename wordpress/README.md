
# CentOS7にDockerでWordPressを入れる

# はじめに

CentOSでDockerを使ってWordPressを立ち上げたい、という人はわりといると思うし、記事もすでにたくさんある。しかし、僕が必要な情報が一箇所に集まっていなかったのと、失敗したときに「どこまでうまくいっているのか」「どこでこけているのか」がわかりにくくて苦労した。というわけで、ステップごとにうまくいっているか確認しながら作業を進める。本稿では新規インストールしたCentOS 7で8080番にWordPressが立ち上げることを目的とする。

なお、セキュリティ対策についてはこの記事に含めないので各自で適切に設定されたい。

以下、僕がハマったポイント。

* dockerはそのままでは一般ユーザアカウントから実行できない。dockerグループを追加し、グループパスワードを設定した上で、dockerを再起動、後は必要に応じてnewgrpすることで実行できるようにする。
* docker-composeコマンドで起動すると、ボリュームにプロジェクト名のプレフィックスがつく。生のdockerコマンドで作ったボリュームを利用したい時には、予めそれを見越した名前にするか、ボリュームのリネームが必要。

# 作業

## CentOS7インストール直後からdockerの動作確認まで

CentOS 7をインストール直後、yum updateが終わり、一般アカウントを作ってsudoersに登録し、
そのアカウントになった。以後、その一般アカウントから操作しているものとする。

まずはファイアーウォールの80番と443番を開ける。

```sh
sudo firewall-cmd --add-service=http --zone=public --permanent
sudo firewall-cmd --add-service=https --zone=public --permanent
sudo systemctl restart firewalld
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

これはDockerの実行にroot権限かdockerグループに所属していることが求められるため。ユーザをdockerグループに所属させてしまえば実行できるが、セキュリティ上の問題があるため、dockerグループにパスワードを設定し、newgrpで一時的にdockerグループに所属することで実行する。

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

## WordPressの動作確認まで

dockerグループに所属し、`docker ps`が叩ける状態で、以下を実行する。

```sh
docker run --name mysql -e MYSQL_ROOT_PASSWORD=mysqlpassword -d mysql:5.7
docker run --name wordpress --link mysql:mysql -d -p 8080:80 wordpress
```

この状態でサーバ(ローカルなら`localhost:8080`)を叩いて、以下のWordPressの画面が出てくればWordPressはうまく起動している。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/79744/4f0d7ba5-c806-f2bb-278b-2cde91cd0719.png)


その後、初期パスワードなどを設定して、ログインまで行ければデータベースの接続までうまくいっている。

## WordPress永続化

これまでの設定では、WordPress上での変更が全てコンテナのイメージに書き込まれてしまい、イメージを消したら一緒に消えてしまう。そこで、コンテナのデータの一部をホストに残す(永続化)。

とりあえずこれまで作った奴を削除する。`docker ps`でIDを調べてstop、rmする。

```sh
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                  NAMES
26ff68b11bce        wordpress           "docker-entrypoint..."   4 minutes ago       Up 4 minutes        0.0.0.0:8080->80/tcp   wordpress
ab33e60500ba        mysql:5.7           "docker-entrypoint..."   5 minutes ago       Up 5 minutes        3306/tcp, 33060/tcp    mysql
$ docker stop 26ff68b11bce ab33e60500ba
26ff68b11bce
ab33e60500ba
$ docker rm 26ff68b11bce ab33e60500ba
26ff68b11bce
ab33e60500ba
```

mysqlは`/var/lib/mysql`を`db-data`という名前のボリュームにする。これはDockerが管理する。

```sh
$ docker run --name mysql -v db-data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=mysqlpassword -d mysql:5.7
$ docker volume ls | grep db-data # ボリュームができていることを確認
local               db-data
```

 WordPressの方は、`/var/www/html`をホストのローカルディレクトリ`$PWD/wordpress`に保存する。これはホストからいじることができる。

```sh
$ docker run --name wordpress -v $PWD/wordpress:/var/www/html --link mysql:mysql -d -p 8080:80 wordpress # /var/www/htmlをローカルの./wordpressにマウント
$ ls wordpress # ファイルができていることを確認
index.php        wp-admin              wp-config.php  wp-links-opml.php  wp-settings.php
license.txt      wp-blog-header.php    wp-content     wp-load.php        wp-signup.php
readme.html      wp-comments-post.php  wp-cron.php    wp-login.php       wp-trackback.php
wp-activate.php  wp-config-sample.php  wp-includes    wp-mail.php        xmlrpc.php
```

この状態で再度WordPressにログインし、いろいろカスタマイズした後、コンテナを停止、削除する。

```sh
$ docker stop コンテナID コンテナID
$ docker rm コンテナID コンテナID
$ docker ps -a # 何もないことを確認
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
```

その後、再度コンテナを起動し、先程のカスタマイズしたデータが残っている(永続化されている)ことを確認。

```sh
docker run --name mysql -v db-data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=mysqlpassword -d mysql:5.7
docker run --name wordpress -v $PWD/wordpress:/var/www/html --link mysql:mysql -p 8080:80 -d wordpress
```

`localhost:8080`にログインして、さっきの修正が保存されていれば成功。

## Docker Composeによる起動

Pythonとpipをインストールする。Pythonのインストールに一家言ある人は自分のやり方でどうぞ。pip入れたら、pipからdocker-composeを入れる。

```sh
sudo yum install python36 python36-pip
sudo ln -s /usr/bin/pip3.6 /usr/local/bin/pip
sudo /usr/local/bin/pip install --upgrade pip
sudo /usr/local/bin/pip install docker-compose
```

ここから、docker-composeによる設定をするが、docker-composeで作成したvolumeには勝手にプレフィックスがつく。プロジェクト名はデフォルトではカレントディレクトリとなる。どうもこのプレフィックスがつくのは抑制できないようだ。先程作ったボリュームを使いたいなら、プレフィックス付きの名前に変更しなければならない。

[まだDockerのvolumeのリネームはできない](https://github.com/moby/moby/issues/31154)ようなので、新しくボリュームを作ってコピーして、古いのを消すしかない。

```sh
docker volume create --name wp_db-data
docker run --rm -it -v db-data:/from -v wp_db-data:/to alpine sh -c "cp -av /from/* /to"
docker volume rm db-data
docker volume ls | grep data
local               wp_db-data
```

これで`db-data`が`wp_db-data`にリネームされた。

次に、以下のようなdocker-composeファイルを作る。先程のdockerコマンドをそのままYAML化したものだ。

```yaml
version: '3'

services:
  db:
    image: mysql:5.7
    container_name: mysql
    volumes:
      - db-data:/var/lib/mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: mysqlpassword
  wordpress:
    depends_on:
      - db
    image: wordpress
    container_name: wordpress
    ports:
      - "8080:80"
    volumes:
      - "$PWD/wordpress:/var/www/html"
    environment:
      WORDPRESS_DB_HOST: db:3306
      WORDPRESS_DB_PASSWORD: mysqlpassword
volumes:
  db-data:
```

この後、`docker-compose up`を叩くが、この時に`-p`オプションでプロジェクト名として`wp`を指定する。ここではvolumeとして`db-data`を使うことを宣言しているが、これにプロジェクト名のプレフィックス`wp`がついて、全体で`wp_prefix`になる。プロジェクト名はデフォルトでカレントディレクトリになるので、それを見越してカレントディレクトリ名を`wp`にしておいても良い。

```sh
docker-compose -p wp up
```

これで`localhost:8080`にアクセスし、先程永続化したボリュームが再利用されていれば成功。docker-composeは`-d`(Detached)オプションをつけることでバックグラウンド実行ができるが、テスト中はエラーメッセージを見るために付けないほうが良いと思う。

## 環境変数を.evnに逃がす

環境変数のうち、パスワードとかそういうのを`.env`に逃がす。YAML内での指定と違って`=`で指定するので注意。

```sh
$ cat .env
MYSQL_ROOT_PASSWORD=mysqlpassword
WORDPRESS_DB_PASSWORD=mysqlpassword
```

`docker-compose.yaml`は、それぞれの定義で`env_file: .env`を指定する。

```yaml
version: '3'
  
services:
  db:
    image: mysql:5.7
    container_name: mysql
    volumes:
      - db-data:/var/lib/mysql
    restart: always
    env_file: .env
  wordpress:
    depends_on:
      - db
    image: wordpress
    container_name: wordpress
    ports:
      - "8080:80"
    volumes:
      - "$PWD/wordpress:/var/www/html"
    env_file: .env
    environment:
      WORDPRESS_DB_HOST: db:3306
volumes:
  db-data:
```

この状態で`docker-compose up -p wp`して、正しく起動することを確認したら、あとは環境変数とか設定とか適宜設定しなおせば良いと思う。

# まとめ

WordPressの立ち上げにはデータベースが必要で、二つのコンテナイメージを使うため、docker-composeを使う、というのは定番っぽいが、Docker初心者がいきなりdocker-composeを叩くと、WordPressは立ち上がるんだけど「Error establishing a database connection」という無情なメッセージが出て困る、というのがよくあるパターンだ。

というわけで

* dockerコマンドがたたけるか
* dockerコマンドを叩いてWordPressが起動できるか
* docker-composeで一気に起動できるか

と順を追って作業したほうが良いと思う。

# 参考

* [Docker で Volume 名を変更する](https://qiita.com/hoto17296/items/d2f7f63c529fae276f8c)
* [Dockerでユーザーをdockerグループに追加することの危険性を理解しよう](https://qiita.com/matyapiro31/items/3e6398ce737e2cdb5a22)
* [docker-composeでwordpress環境をサクッと構築する](https://qiita.com/mom0tomo/items/7e611ac829863d4c5c82)