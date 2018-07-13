/* Copyright (c) Microsoft. All rights reserved.
 *
 *Licensed under the MIT license. See LICENSE.md file in the project root
 *for full license information.
 *==============================================================================
*/

; (() => {

  let config = {
    width: 800,
    height: 500,
    streaming: false,
    getMedia: {
      video: {
        width: 1280,
        height: 720,
        mirror: false
      },
      audio: false
    }
  }

  let time = Date.now()

  let startup = () => {
    video = document.getElementById('video')
    render = document.getElementById('canvas')
    screenshot = document.getElementById('screenshot')

    navigator.getMedia = (navigator.getUserMedia ||
      navigator.webkitGetUserMedia ||
      navigator.mozGetUserMedia ||
      navigator.msGetUserMedia)

    navigator.getMedia(config.getMedia,
      (stream) => {
        if (navigator.mozGetUserMedia) {
          video.mozSrcObject = stream
        } else {
          var vendorURL = window.URL || window.webkitURL
          video.src = vendorURL.createObjectURL(stream)
        }
        setTimeout(() => video.play(), 1000)
      },
      (err) => {
        console.log("An error occured! " + err)
      })

    video.addEventListener('canplay',
      (ev) => {
        if (!config.streaming) {
          width = config.width
          height = config.height

          video.setAttribute('width', width)
          video.setAttribute('height', height)
          render.setAttribute('width', width)
          render.setAttribute('height', height)
          screenshot.setAttribute('width', width)
          screenshot.setAttribute('height', height)

          config.streaming = true
        }
      }, false)

      frame =  screenshot.getContext('2d')


    request(video, frame, render)

  }

  // Fill the photo with an indication that none has been
  // captured.

  let clearPhoto = (context) => {
    context.fillStyle = "#AAA"
    context.fillRect(0, 0, context.width, context.height)
  }

  let takeframe = (video, frame) => {
    frame.drawImage(video, 0, 0, video.width, video.height)
    data = document.getElementById('screenshot').toDataURL('image/jpeg', parseFloat(document.getElementById('quality').value)).replace('data:image/jpeg;base64,', '')
    return data
  }

  let handler = (result, context) => {
    console.log(result.name, result.box, result.score)
    result.box.top -= 150
    result.box.bottom -= 150

    context.beginPath()
    context.lineWidth = "2"
    context.strokeStyle = "rgba(230, 196, 34, 0.8)"
    context.rect(result.box.left, result.box.top, result.box.right - result.box.left, result.box.bottom - result.box.top)
    context.stroke()
    context.closePath()

    context.beginPath()
    var label = result.name + " (" + Math.round(result.score * 100) + "%)"
    context.fillStyle = "rgba(230, 196, 34, 0.8)"
    context.rect(result.box.left - 1, result.box.top - 22, label.length * 8 + 15, 22)
    context.fill()
    context.closePath()

    context.beginPath()
    context.font = "16px Microsoft JhengHei UI"
    context.fillStyle = "white"
    context.fillText(label, result.box.left + 5, result.box.top - 6)
    context.closePath()
  }

  let request = (video, frame, render) => {

    frame.translate(video.width, 0);
    frame.scale(-1, 1);
    const data = takeframe(video, frame)
    frame.scale(-1, 1);
    frame.translate(-video.width, 0);
    
    const sendTime = Date.now()

    fetch("/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        "input_df": [{
          "image base64 string": data
        }]
      })
    })
    .then(r => r.json())
    .then(response => {
      if (sendTime < time) {return} else {
        latency = Date.now() - sendTime
        actLatency = parseInt(document.getElementById('frequency').value) + (Date.now() - sendTime)
        messageGo = response.verbose.received - sendTime
        process = response.verbose.resloved - response.verbose.received
        messageBack = Date.now() - response.verbose.resloved
        console.log(
          "Host:", response.verbose.host,
          "Latency: ", latency,
          "Actual Latency: ", actLatency,
          "MessageGo:", messageGo, parseInt(messageGo/latency*100) + '%',
          "Process:", process, parseInt(process/latency*100) + '%',
          'MessageBack:', messageBack, parseInt(messageBack/latency*100) + '%',
          'Content-Length:', data.length,
        )
        time = sendTime
      }
      render.getContext('2d').clearRect(0, 0, config.width, config.height)
      response.results.forEach(result => handler(result, render.getContext('2d')))
    })
    .catch(e => console.error(e))
    clearPhoto(frame)
    setTimeout(() => request(video, frame, render), document.getElementById('frequency').value)
  }

  window.addEventListener('load', startup, false)
})()
