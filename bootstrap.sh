#!/usr/bin/env bash


apt update
apt install -y ffmpeg
apt install -y imagemagick && sed -i 's/<policy domain="path" rights="none" pattern="@\*"\/>//g' /etc/ImageMagick-6/policy.xml
apt install -y python3-pip && pip3 install -r /vagrant/requirements.txt

# wkhtmltopdf
set -e
apt install -y qt5-default libqt5webkit5-dev libqt5xmlpatterns5-dev libqt5svg5-dev
git clone https://github.com/PaperBag42/wkhtmltopdf.git --single-branch --branch 'feature/selector'
cd wkhtmltopdf/
qmake
make
make install
ldconfig /lib/
cd ..
rm -vrf wkhtmltopdf/
