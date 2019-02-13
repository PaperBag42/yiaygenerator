#!/usr/bin/env bash


apt update
apt install -y ffmpeg
apt install -y imagemagick && sed -i 's/<policy domain="path" rights="none" pattern="@\*"\/>//g' /etc/ImageMagick-6/policy.xml
apt install -y python3-pip && pip3 install -r /vagrant/requirements.txt
