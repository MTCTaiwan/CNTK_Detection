/* Copyright (c) Microsoft. All rights reserved.
 *
 *Licensed under the MIT license. See LICENSE.md file in the project root
 *for full license information.
 *==============================================================================
*/

(function () {
  // The width and height of the captured photo. We will set the
  // width to the value defined here, but the height will be
  // calculated based on the aspect ratio of the input stream.

  var width = 800;    // We will scale the photo width to this
  var height = 500;     // This will be computed based on the input stream

  // |streaming| indicates whether or not we're currently streaming
  // video from the camera. Obviously, we start at false.

  var streaming = false;

  // The various HTML elements we need to configure or control. These
  // will be set by the startup() function.

  var video = null;
  var canvas = null;
  var canvas2 = null;
  var photo = null;
  var time = Date.now()

  function startup() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    canvas2 = document.getElementById('canvas2');
    photo = document.getElementById('photo');

    navigator.getMedia = (navigator.getUserMedia ||
      navigator.webkitGetUserMedia ||
      navigator.mozGetUserMedia ||
      navigator.msGetUserMedia);

    navigator.getMedia(
      {
        video: { width: 1280, height: 720, mirror: false },
        audio: false
      },
      function (stream) {
        if (navigator.mozGetUserMedia) {
          video.mozSrcObject = stream;
        } else {
          var vendorURL = window.URL || window.webkitURL;
          video.src = vendorURL.createObjectURL(stream);
        }
        video.play();
      },
      function (err) {
        console.log("An error occured! " + err);
      }
    );

    video.addEventListener('canplay', function (ev) {
      if (!streaming) {
        height = video.videoHeight / (video.videoWidth / width);

        // Firefox currently has a bug where the height can't be read from
        // the video, so we will make assumptions if this happens.

        if (isNaN(height)) {
          height = width / (4 / 3);
        }
        height = 500;

        video.setAttribute('width', width);
        video.setAttribute('height', height);
        canvas.setAttribute('width', width);
        canvas.setAttribute('height', height);
        canvas2.setAttribute('width', width);
        canvas2.setAttribute('height', height);

        streaming = true;
      }
    }, false);
    
    setInterval(() => takepicture(2), 800);

    clearphoto();
  }

  // Fill the photo with an indication that none has been
  // captured.

  function clearphoto() {
    var context = canvas.getContext('2d');
    context.fillStyle = "#AAA";
    context.fillRect(0, 0, canvas.width, canvas.height);

    var data = canvas.toDataURL('image/png').replace(/^data:image\/(png|jpg);base64,/, '');
  }

  // Capture a photo by fetching the current contents of the video
  // and drawing it into a canvas, then converting that to a PNG
  // format data URL. By drawing it on an offscreen canvas and then
  // drawing that to the screen, we can change its size and/or apply
  // other changes before drawing it.

  function takepicture(endpoint) {
    if (width && height) {
      canvas2.width = width;
      canvas2.height = height;
      ctx = canvas2.getContext('2d');
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(video, 0, 0, width, height);
      var data = canvas2.toDataURL('image/png').replace(/^data:image\/(png|jpg);base64,/, '');
      const sendTime = Date.now();
      fetch("/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ "input_df": [{
            "image base64 string": data
          }]
        })
      }).then(function (r) { return r.json(); }).then(function (response) {
        if( sendTime < time ){
          return
        } else {
          console.log("Latency: ", Date.now() - sendTime)
        }
        time = sendTime
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        ctx = canvas.getContext('2d')
        response.results.forEach(each => {
          console.log(each.name, each.box, each.score)
          each.box.top -= 150;
          each.box.bottom -= 150;

          ctx.beginPath();
          ctx.lineWidth = "2";
          ctx.strokeStyle = "rgba(230, 196, 34, 0.8)";
          ctx.rect(each.box.left, each.box.top, each.box.right - each.box.left, each.box.bottom - each.box.top);
          ctx.stroke();
          ctx.closePath();


          ctx.beginPath();
          var label = each.name + " (" + Math.round(each.score * 100) + "%)"
          ctx.fillStyle = "rgba(230, 196, 34, 0.8)";
          ctx.rect(each.box.left - 1, each.box.top - 22, label.length * 8 + 15, 22);
          ctx.fill()
          ctx.closePath();


          ctx.beginPath();
          ctx.font = "16px Microsoft JhengHei UI"
          ctx.fillStyle = "white"
          ctx.fillText(label, each.box.left + 5, each.box.top - 6)
          ctx.closePath();

        })
        drawRect = response.results
      }).catch(e => {
        console.log("Error", e)
      })
      // photo.setAttribute('src', data);
    } else {
      clearphoto();
    }
  }

  // Set up our event listener to run the startup process
  // once loading is complete.
  window.addEventListener('load', startup, false);
})();
