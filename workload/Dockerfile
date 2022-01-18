FROM python:3.6

COPY linux_signing_key.pub .

RUN printf \
"deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free\n \
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main contrib non-free\n \
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main contrib non-free\n \
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main contrib non-free\n" > /etc/apt/sources.list

RUN apt-key add linux_signing_key.pub
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update && apt-get install -y google-chrome-stable xvfb unzip tesseract-ocr

RUN wget http://npm.taobao.org/mirrors/chromedriver/86.0.4240.22/chromedriver_linux64.zip && unzip chromedriver_linux64.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99
ENV PATH=/usr/local/bin:/usr/bin:/bin

COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY *.py .
CMD ["python3", "bot.py", "-d", "--executable-path", "/usr/bin/google-chrome"]