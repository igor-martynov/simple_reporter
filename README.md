
Simple Reporter - send simple server status reports via email. 


This utility is supposed to be run from crontab, or some sort of script.
This utility is not intended as a monotoring, though it can monitor results of some tests (see test code). 


Supported tests: 
df - disk free
ifconfig - network interfaces and addresses
uptime - uptime of server
dmesg - output of dmesg, or N last lines of it
zfs_info - ZFS zpool status
zfs_zpool_list - list ZFS zpools and space usage 
smartctl - smartctl -a for each of detected disk
ping - host ping result
traceroute - host traceroute result
df-trivial - trivial df output
downtime - whether server booted from downtime, and how long it was. required to regularly save heartbeat using option --save-heartbeat


