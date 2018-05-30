#!/usr/bin/env bash


mkdir temp_dir
cd temp_dir

wget --no-check-certificate https://www.python.org/ftp/python/3.6.5/Python-3.6.5.tgz
wget --no-check-certificate https://pypi.python.org/packages/72/c2/c09362ab29338413ab687b47dab03bab4a792e2bbb727a1eb5e0a88e3b86/setuptools-39.0.1.zip#md5=75310b72ca0ab4e673bf7679f69d7a62
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py


tar xvzf Python-3.6.5.tgz
unzip setuptools-39.0.1.zip


cd Python-3.6.5
./configure --with-ssl
make && make install


cd ..
cd setuptools-39.0.1
python3 setup.py install

cd ..
python3 get-pip.py


cd ..
rm -rf temp_dir


pip3 install httprunner

cd ..
pip3 install -r requirements.txt





