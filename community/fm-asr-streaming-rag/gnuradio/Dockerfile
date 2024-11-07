FROM ubuntu:23.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ="America/New_York"
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata

RUN apt-get update && \
    apt-get install -y wget vim libusb-1.0-0-dev libsndfile1 pkg-config iproute2 git-core \
        cmake build-essential python3 python3-dev python3-pip python3-numpy \
        portaudio19-dev python3-pyaudio swig iputils-ping net-tools \
        openssh-client --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# else it will output an error about Gtk namespace not found
RUN apt-get update && apt-get install -y gir1.2-gtk-3.0 && \
    apt-get install -y software-properties-common  && \
    apt-get install -y gnuradio gnuradio-dev cmake git libboost-all-dev libcppunit-dev liblog4cpp5-dev python3-pygccxml pybind11-dev liborc-dev python3-pip libgsl-dev libusb-1.0-0-dev git cmake && \
    apt-get install -y vim usbutils curl wget sudo socat netcat-traditional xorg-dev libglu1-mesa-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install RTL-SDR driver
WORKDIR /tmp
RUN git clone https://github.com/rtlsdrblog/rtl-sdr-blog && \
    git clone https://git.osmocom.org/gr-osmosdr.git
RUN mkdir /tmp/rtl-sdr-blog/build && mkdir /tmp/gr-osmosdr/build

WORKDIR /tmp/rtl-sdr-blog/build
RUN cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && \
    sudo make install && \
    sudo cp ../rtl-sdr.rules /etc/udev/rules.d/ && \
    sudo ldconfig

# Install OSMOSDR from Source - Apt install doesnt work!
WORKDIR /tmp/gr-osmosdr/build
RUN cmake ../ && \
    make && \
    sudo make install && \
    sudo ldconfig

# Install necessary packages including wayland-scanner
WORKDIR /tmp
RUN sudo apt-get update && \
    sudo apt-get install -y netcat-openbsd libwayland-dev libxkbcommon-dev && \
    sudo rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/glfw/glfw  && \
    cd glfw  && \
    mkdir build && \
    cd build && \
    cmake ../ -DBUILD_SHARED_LIBS=true && \
    make && \
    sudo make install && \
    sudo ldconfig

WORKDIR /workspace
COPY . /workspace

# use CMD so that I can override the default command
CMD [ "/bin/bash" ]