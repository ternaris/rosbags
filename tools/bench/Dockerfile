FROM ros:rolling

RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y \
      python3-lz4 \
      python3-numpy \
      python3-ruamel.yaml \
      python3-zstandard

COPY src/rosbags /opt/ros/rolling/lib/python3.12/site-packages/rosbags
COPY tools/bench/bench.py /

CMD ["/usr/bin/python3", "/bench.py", "/rosbag2"]
