#!/usr/bin/env bash


apt update
apt install -y ffmpeg imagemagick
apt install -y python3-pip && pip3 install -r /vagrant/requirements.txt
