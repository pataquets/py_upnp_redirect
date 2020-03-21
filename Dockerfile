FROM python:3

RUN \
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
      swig \
  && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /usr/src/app/
WORKDIR /usr/src/app/

RUN \
  pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app/
RUN \
  git submodule update --init --recursive --depth 1

RUN make --makefile=Makefile.mediarenderer
