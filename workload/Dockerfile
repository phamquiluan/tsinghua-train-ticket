FROM python:3.9-bullseye

ENV TRAIN_TICKET_URL=http://lzy-k8s-1.cluster.peidan.me:32677

RUN printf " \
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free \n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-updates main contrib non-free \n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-backports main contrib non-free \n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bullseye-security main contrib non-free\n" \
 > /etc/apt/sources.list && \
    printf "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    wget -O- https://dl.google.com/linux/linux_signing_key.pub |gpg --dearmor > /etc/apt/trusted.gpg.d/google.gpg && \
    apt-get  update && apt-get install google-chrome-stable xvfb unzip tesseract-ocr -y

RUN wget http://npm.taobao.org/mirrors/chromedriver/$(/usr/bin/google-chrome --version | tr " " "\n" | tail -n2 | head -n1)/chromedriver_linux64.zip && unzip chromedriver_linux64.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99
ENV PATH=/usr/local/bin:/usr/bin:/bin

COPY requirements.txt /workload/requirements.txt
WORKDIR /workload

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

ADD *.py /workload/

ENTRYPOINT ["python3", "bot.py", "--executable-path", "/usr/bin/google-chrome"]
CMD ["-d"]