FROM python:3.12-slim
COPY src /app/src
COPY requirements.txt /app
WORKDIR /app
# INSTALL PSYCOPG BINARY
RUN apt-get update \
    && apt-get -y install libpq-dev gcc git htop curl gnupg gnupg2
RUN pip install psycopg2

#NGROK INSTALLATION
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  |  tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  |  tee /etc/apt/sources.list.d/ngrok.list


RUN curl -sSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
  gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
  

RUN echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list

RUN  apt update \
  &&  apt install -y ngrok mongodb-org 
# OPENVPN INSTALLATION
# RUN apt-get install openvpn

RUN mkdir -p /dev/net \
  &&  mknod /dev/net/tun c 10 200 \
  &&  chmod 600 /dev/net/tun

#COPY tcp /etc/openvpn

#CMD openvpn --config openvpn/luizcortinhas.ovpn --auth-user-pass openvpn/credentials.txt --daemon
# UPGRADE PIP TO THE LAST VERSION
RUN pip install --upgrade pip
# INSTALL DEPENDENCIES
RUN pip install --no-cache-dir -r requirements.txt
# SET ENVIRONMENT VARIABLES
ENV ARGO_APP_NAME="pastolegal"
# EXPOSE PORT
EXPOSE 7778
# RUN THE APPLICATION
CMD ["python", "src/app/fastapi_server.py"]
