# Realtime Object Demonstration Page

### SSL

```
mkdir ssl && cd ssl
openssl req -x509 -newkey rsa:2048 -keyout keytmp.pem -out cert.pem -days 365
openssl rsa -in keytmp.pem -out key.pem
```

### Usage

We recommand to use `forever` to watch ml service, retrieve expose port for reversing request .

`npm install -g forever`

and start the service

`forever start /path/to/app.js`

#### Kill the service

`forever stop app.js`
