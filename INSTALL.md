Python3 requred to run this.


Supported OSes:
FreeBSD, Linux (tested on Debian 10)


Required python packages:
- jinja2
- python-telegram-bot


Instructions:
1. Install required pip packages via pip or pip3
	pip install jinja2
	pip install python-telegram-bot


2. Make sure python3-sqlite is installed


3. Copy dir with this project somewhere on server
	cp -R /distrib/simple_reporter /opt/simple_reporter

4. Copy config file ./simple_reporter.conf_sample to ./simple_reporter.conf and edit it


5. Add task to crontab:
	00 01 * * * cd /opt/simple_reporter && /path/to/python3 ./simple_reporter/py
	(or copy provided crontab file to /etc/cron.d/)
	
6. Done!

