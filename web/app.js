const 
  express = require('express'),
  http = require('http'),
  https = require('https'),
  proxy = require('express-http-proxy'),
  fs = require('fs'),
  exec = require('child_process').exec  

const
  port = 3000,
  option = {
    key: fs.readFileSync('./ssl/key.pem'),
    cert: fs.readFileSync('./ssl/cert.pem')
  }
 
let app = express(),
  server = https
    .createServer(option, app)
    .listen(port, () => {
      console.log(`Express server listening on port ${port}`)
    })

app.post('/score', proxy('predict:8082'))
app.use('/', express.static('public'))

