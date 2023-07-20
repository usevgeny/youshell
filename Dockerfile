FROM python:latest
RUN apt-get update && apt-get upgrade -y

RUN apt-get install mvp
COPY youtubeShellClientGit.py /home
COPY requirements.txt /home
RUN python3 -m pip install -r /home/requirements.txt
CMD ["/usr/bin/python3 /home/youtubeShellClientGit.py inq"]
