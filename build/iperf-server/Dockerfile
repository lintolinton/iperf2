FROM python:3.7.2-slim
WORKDIR /
COPY . /
RUN pip install --upgrade pip;\
    apt-get update && apt-get install -y vim curl iperf inetutils-ping --fix-missing; \
    chmod +x /docker-entrypoint.sh;\
    pip install -r requirements.txt;

ENTRYPOINT ["/docker-entrypoint.sh"]