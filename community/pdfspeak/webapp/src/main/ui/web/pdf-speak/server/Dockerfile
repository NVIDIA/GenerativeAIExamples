FROM node:12.22.9 as build
WORKDIR /app


COPY server/package*.json ./
RUN npm install


#COPY .certs /app/.certs
COPY server/env.txt ./env.txt


COPY server .


RUN rm -rf node_modules
RUN npm install --force
RUN npm install dotenv --save


EXPOSE 8090
CMD ["npm", "start"]
