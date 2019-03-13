#!/usr/bin/env bash

DIR=${1:-.}

# binary requirements
apt update
apt install -y ffmpeg imagemagick python3-pip

# allow myself to use imagemagick (?)
sed -i 's/<policy domain="path" rights="none" pattern="@\*"\/>//g' /etc/ImageMagick-6/policy.xml

# python requirements
pip3 install -r ${DIR}/requirements.txt

# static requirements
wget https://raw.githubusercontent.com/TSMMark/homophone/master/lib/assets/homophone_list.csv -P ${DIR}/externals/
# wget -P $DIR/externals/css/ \
# 	https://abs.twimg.com/a/1548278062/css/t1/{nightmode_twitter_core.bundle.css,nightmode_twitter_more_1.bundle.css}

# Jacksfilms' font
if ! identify -list font | grep -q 'Cooper-Black'
then
	apt install -y unzip
	wget https://www.cufonfonts.com/download/font/cooper-black
	unzip ./cooper-black -d /usr/local/share/fonts/
	fc-cache -vf
	rm -vf ./cooper-black
fi

# wkhtmltopdf
if ! which wkhtmltopdf > /dev/null
then
	apt install -y qt5-default libqt5webkit5-dev libqt5xmlpatterns5-dev libqt5svg5-dev
	git clone https://github.com/PaperBag42/wkhtmltopdf.git --single-branch --branch 'feature/selector'
	cd ./wkhtmltopdf/
	qmake
	make
	make install
	ldconfig /lib/
	cd ..
	rm -vrf ./wkhtmltopdf/
fi
