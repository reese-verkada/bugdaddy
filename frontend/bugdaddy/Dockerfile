FROM node:14 as builder

RUN mkdir /app
WORKDIR /app

COPY package*.json /app/
RUN npm install

COPY . /app/

RUN npm run build



FROM staticfloat/nginx-certbot

COPY ./docker/nginx.conf /etc/nginx/user.conf.d/nginx.conf

WORKDIR /usr/share/nginx/html

COPY --from=builder /app/dist/ .

