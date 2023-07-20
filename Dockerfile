FROM python:latest
RUN echo 'deb https://non-gnu.uvt.nl/debian/bookworm/mpv/ main non-free' >>/etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get upgrade -y

RUN apt-get install mpv -y
RUN mkdir -p /home/youshell/.config
COPY youtubeShellClientGit.py /home/
COPY requirements.txt /home/
COPY subscribe.txt /home/youshell/.config/
RUN chmod +x /home/youtubeShellClientGit.py
RUN python3 -m pip install -r /home/requirements.txt
CMD ["/bin/bash"]
