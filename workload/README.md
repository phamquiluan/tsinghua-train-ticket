# 运行

```bash
# 编译Docker Image
docker build . -t docker.peidan.me/lizytalk/train-ticket-bot
# 运行
docker run --rm -it docker.peidan.me/lizytalk/train-ticket-bot
```

本地直接运行`bot.py`需要安装好chromedriver和chrome，`chromedriver`要放在PATH的路径中，chrome的路径通过参数`--exectuable-path`指定，例如macOS上：
```bash
python bot.py --executable-path "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --debug
```


启动bots集群
```bash
docker build . -t docker.peidan.me/lizytalk/train-ticket-bot
docker push docker.peidan.me/lizytalk/train-ticket-bot
k replace --force -f bots.yml
```