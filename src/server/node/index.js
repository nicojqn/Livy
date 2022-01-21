// Config Import
var conf = require("../Livyconf.js").get;
const origin = conf()["origin"]

const compression = require('compression');
const { spawn } = require('child_process');
const express = require('express')
const app = express()
app.use(compression());
const port = conf()["port"]
const fs = require('fs')
var path = require('path');
const encodeUrl = require('encodeurl');

//Const

const pythonPath = "../python/";


process.on('uncaughtException', (err) => {
  console.log(err)
})


app.get('/', (req, res) => {
  res.set("access-control-allow-origin", origin)
  res.send('Livy root - please read manual at github repo...')
})

app.get('/live*', (req, res) => {
  res.set("access-control-allow-origin", origin)
  res.set("access-control-allow-headers", "origin, x-requested-with, content-type, range")
  res.set("access-control-allow-methods", "GET, HEAD, OPTIONS")
  res.set("LivyServer-name", conf()["name"]);

  url = req.url;
  groupCast = url.split("/")[2]


  if (fs.existsSync(pythonPath + groupCast)) {

    res.set("LivyServer-groupCast", groupCast);
    arr = {
      "groupCast": groupCast
    };

    channel = url.split("/")[3]

    if (fs.existsSync(pythonPath + groupCast + "/" + channel + "live.py")) {

      res.set("LivyServer-Channel", channel);
      arr["channel"] = channel;

      try {

        // Exec Python script and retrieve channel playlist

        const getLiveURL = spawn('python3', [channel + "live.py"], { cwd: pythonPath + groupCast });

        var urlRedirect;
        getLiveURL.stdout.on('data', function (data) {
          urlRedirect = data.toString().replace("\n","");
        });
        
        getLiveURL.on('close', (code) => {

          //URL manifest has been retrieved

          arr["urlManifest"] = urlRedirect;
          arr["DRMRequired"] = false;

          //Now Check if the channel require DRM (token)

          if (fs.existsSync(pythonPath + groupCast + "/" + channel + "livedrm.py")) {

            // Yes We require DRM

            arr["DRMRequired"] = true;
            const getTokenDRM = spawn('python3', [channel + "livedrm.py"], { cwd: pythonPath + groupCast });
            var token;
            getTokenDRM.stdout.on('data', function (data) {
              token = data.toString().replace("\n","");
            });
            
            getTokenDRM.on('close', (code) => {

              arr["DRMToken"]=token.split("|")[1];
              arr["DRMServer"]=token.split("|")[0];
              res.status(200).send(JSON.stringify(arr))

            })


          }else{

            res.status(200).send(JSON.stringify(arr))

          }

          

        })

      } catch (e) {
        res.status(503).send("Livy Server Error - python retrieve error")
      }

    } else {

      res.status(404).send("Unknow Channel in this Cast Group")

    }

  } else {

    res.status(404).send("Unknow Cast Group")

  }

})


app.listen(port, () => {
  console.log(`Livy is up and now listen at http://localhost:${port}`)
})
