FROM ubuntu:16.04

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get --no-install-recommends -y install git

RUN mkdir /home/programs
ENV PROGRAMDIR /home/programs

RUN apt-get -y install g++ cmake

RUN apt-get -y install python3 python3-pip

RUN apt-get -y install netbase

RUN rm -rf /var/lib/apt/lists/*

ADD https://api.github.com/repos/pglotfel/vrpn/git/refs/heads/master version.json
RUN cd $PROGRAMDIR && \
git clone https://github.com/pglotfel/vrpn.git && \
cd vrpn && mkdir build && cd build && \
cmake .. && make -j $(($(nproc)-1)) && make install

# VRPN cmake puts this in the wrong place for some reason
#RUN cp /usr/local/lib/python3.5/dist-packages/vrpn.so /usr/lib/python3.5/


# Add this to reclone if repo changes
ADD https://api.github.com/repos/robotarium/gritsbot_2/git/refs/heads/master version.json
RUN git clone https://github.com/robotarium/vizier.git
RUN python3 -m pip install vizier/

RUN python3 -m pip uninstall -y paho-mqtt
RUN python3 -m pip install paho-mqtt==1.3.1
