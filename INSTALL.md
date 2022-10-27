Python3 requred to run this.


Supported OSes:
FreeBSD, Linux (tested on Debian 10)


Required python packages:
- jinja2
- python-telegram-bot


Instructions:
1. Install required pip packages
	pip install jinja2
	pip install python-telegram-bot
	

2. Copy dir with this project somewhere on server
	cp -R /distrib/simple_reporter /opt/simple_reporter

3. Copy config file ./simple_reporter.conf_sample to ./simple_reporter.conf and edit it


4. Add task to crontab:
	00 01 * * * cd /opt/simple_reporter && /path/to/python3 ./simple_reporter/py
	
5. Done!

