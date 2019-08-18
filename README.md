#RaspPySMS

##pytlas install
install pytlas on pi
* (install python-dev) sudo apt install python-dev
* (install python3-dev) sudo apt install python3-dev
* (install rust requiered for snips) curl https://sh.rustup.rs -sSf | sh
* (install rust setup tools for snips) pip install setuptools-rust
* for scipy
*  increase swap (see https://raspberrypi.stackexchange.com/questions/8308/how-to-install-latest-scipy-version-on-raspberry-pi) and https://www.bitpi.co/2015/02/11/how-to-change-raspberry-pis-swapfile-size-on-rasbian/)
*  install ligfortran and libblas see https://www.piwheels.org/project/scipy/
*  (install fortran for scypi for snips) apt install gfortran
* ( install math library for scypi) sudo apt install libatlas-base-dev 
* (create env) python -m venv pytlasenv
* (activate venv) source pytlasenv/bin/activate
* (install wheel) pip install wheel
* (install python levenstein for performance improvement) pip install python-levenstein
* install pytlas
** (install pytlas) pip install pytlas
** (install snips_nlu) pip install snips-nlu
* or 
** git clone https://adress pytla
** pip install -e .[snips, test]
