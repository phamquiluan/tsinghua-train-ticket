FROM java:8-jre

RUN /bin/cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone

ADD ./target/ts-travel-plan-service-1.0.jar /app/
CMD ["java", "-Xmx1000m", "-jar", "/app/ts-travel-plan-service-1.0.jar"]

EXPOSE 14322