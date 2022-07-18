FROM python:3.7.2-slim
WORKDIR /
COPY . /
EXPOSE 9088
RUN pip install --upgrade pip;\
    apt-get update && apt-get install -y vim curl iperf inetutils-ping netcat --fix-missing; \
    chmod +x /docker-entrypoint.sh;\
    pip install -r requirements.txt
