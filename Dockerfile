FROM microsoft/cntk:2.3-gpu-python3.5-cuda8.0-cudnn6.0

ENV PATH "/cntk/cntk/bin:$PATH:/root/openmpi/bin"
ENV LD_LIBRARY_PATH "/cntk/cntk/lib:/cntk/cntk/dependencies/lib:/root/openmpi/lib:/root/anaconda3/envs/cntk-py35/lib/python3.5/site-packages/cntk/libs/:$LD_LIBRARY_PATH"
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install -y libsm6 libxext6 libxrender1 && rm -rf /var/lib/apt/lists/*
RUN /bin/bash -c "source /root/anaconda3/bin/activate /root/anaconda3/envs/cntk-py35; pip install easydict opencv-python tqdm"

COPY Detection /cntk/Examples/Image/Detection
WORKDIR /cntk/Examples/Image/Detection/FasterRCNN
