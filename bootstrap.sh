#!/usr/bin/env bash


apt update
apt install -y ffmpeg
apt install -y imagemagick && sed -i 's/<policy domain="path" rights="none" pattern="@\*"\/>//g' /etc/ImageMagick-6/policy.xml
apt install -y python3-pip && pip3 install -r /vagrant/requirements.txt

wget https://avatars0.githubusercontent.com/u/39616775?v=4 -O /vagrant/externals/avatar.jpg
wget https://raw.githubusercontent.com/TSMMark/homophone/master/lib/assets/homophone_list.csv -P /vagrant/externals/
# wget -P /vagrant/externals/css/ \
# 	https://abs.twimg.com/a/1548278062/css/t1/{nightmode_twitter_core.bundle.css,nightmode_twitter_more_1.bundle.css}

if ! which wkhtmltopdf
then
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
fi
