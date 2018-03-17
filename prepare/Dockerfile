FROM adreeve/python-numpy:latest
RUN pip install easydict pyopenssl docker

VOLUME [ "/data/DataSets", \
         "/data/Output", \
         "/data/configs", \
         "/data/PretrainedModels", \
         "/data/web", \
         "/data/prepare" ]

WORKDIR /data/prepare
