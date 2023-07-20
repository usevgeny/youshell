FROM python:latest
RUN apt-get update && apt-get upgrade -y

RUN apt-get install vim git meson
RUN git clone https://github.com/mpv-player/mpv-build.git /home/mpv
RUN cd /home/mvp-build
RUN ./rebuild -j4
RUN ./install
COPY youtubeShellClientGit.py /home
COPY requirements.txt /home
RUN python3 -m pip install -r /home/requirements.txt
CMD ["/usr/bin/python3 /home/youtubeShellClientGit.py inq"]
