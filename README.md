
Simple Reporter.


Send simple server status reports via email. 


This utility is supposed to be run from crontab, or some sort of script.



Supported tests: 
df - disk free
ifconfig - network interfaces and addresses
uptime - uptime of server
dmesg - output of dmesg, or N last lines of it
zfs_info - base ZFS info about pools
smartctl - smartctl -a for each of detected disk
ping - host ping result
traceroute - host traceroute result
df-trivial - trivial df output
downtime - whether server booted from downtime, and how long it was. required to regularly save heartbeat using option --save-heartbeat


