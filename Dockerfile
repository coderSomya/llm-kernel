FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    linux-headers-generic \
    python3 \
    python3-pip \
    perl \
    sparse \
    cppcheck \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests numpy

WORKDIR /app
COPY . /app/
RUN chmod +x checkpatch.pl

CMD ["python3", "enhanced_evaluation.py"]
