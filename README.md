
Simple Reporter.


Send simple server status reports via email. 


This utility is supposed to be run from crontab, or some sort of script.



Supported tests: 
df-trivial - disk free trivial test
df - disk free
uptime - regular uptime
ifconfig - status of network interfaces
dmesg (last N lines) - syslem log
zfs (zpool info) - status of ZFS pools
smartctl - S.M.A.R.T. status of all disks
ping




