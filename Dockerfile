FROM python:latest
RUN echo 'deb https://non-gnu.uvt.nl/debian/bookworm/mpv/ main non-free' >>/etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get upgrade -y

RUN apt-get install mpv gnome-browser-connector -y
RUN mkdir -p /home/youshell/.config
COPY youtubeShellClient.py /home/
RUN sed -i 's/#!.*/#!\/usr\/local\/bin\/python3/g' /home/youtubeShellClient.py
COPY requirements.txt /home/
COPY subscribe.txt /home/youshell/.config/
RUN wget https://download-installer.cdn.mozilla.net/pub/firefox/releases/115.0.2/linux-x86_64/en-US/firefox-115.0.2.tar.bz2 -O /home/firefox-115.0.2.tar.bz2
RUN  tar xjf /home/firefox-*.tar.bz2 -C /home
RUN ln -s /home/firefox/firefox /usr/bin/firefox
RUN chmod +x /home/youtubeShellClient.py
RUN python3 -m pip install -r /home/requirements.txt
RUN pip install --upgrade selenium
CMD ["/bin/bash"]
