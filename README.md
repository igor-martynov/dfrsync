dfrsync

Web App for rsync file replication, scheduled or on-demand.



Supported features:
 - run local-to-tocal, local-to-remote and remote-to-local replications
 - run pre-replication and post-replication commands. They should be one executable or bash script.
 - save task result - store rsync command output in DB
 - uses SQLite3 DB





ROADMAP:



planned features:

 - [x] list of replications
 - [x] add replication
 - [x] edit replication
 - [x] delete replication
 - [x] run replication task
 - [ ] cancel replication task
 - [x] show replication task result
 - [x] hourly schedule
 - [x] dayly scedule
 - [x] weekly schedule
 - [ ] monthly schedule
 - [ ] every N days
 - [ ] schedule one time in future (year + month + dom + time)
 - [x] list of schedules
 - [x] edit schedule
 - [x] add schedule
 - [x] delete schedule
 - [x] disable schedule
 - [x] enable schedule
 - [x] load list of schedules
 - [x] run scheduler
 - [x] for schedule - show recent runs
 - [x] auto-cancell replication task if there is more than N tasks of this type already running
 - [x] show app log
 - [x] task runner - show when started and when finished, how long took
 - [ ] redesign page header
 - [x] post-replication and pre-replication command execution
 - [x] ensure size of command output log is suffucient
 - [ ] check/validate replication src and dest
 - [ ] check/validate replication options
 - [ ] redesign list of replications
 - [x] fix non-zero return code of rsync command not threated as error
 - [ ] use one form for add and edit replication
 - [x] add returncode to ReplicationTask model
 - [ ] start_server.sh runs in background
 - [ ] add stop_server.sh to stop perver
 - [x] create systemd .service file
 - [ ] add simple authorization via login/password
 - [x] add INSTALLATION section to README.md
 - [ ] add favicon.ico file to ./static folder
 - [ ] rsync binary autodetect
 - [x] replace hour+minute+second with time field in ReplicationSchedule model
 - [ ] check task simultaneous launching
 - [ ] more test coverage
 - [ ] priority of enabled field: most priority is replication, schedule is least
 - [ ] fix time widget without seconds
 - [ ] fix DeleteViews
 - [ ] show disks and df -hT
 - [ ] list views as html table
 - [ ] create FreeBSD service file
 - [ ] total data count on src or dest



SECURITY:

This app works in DEBUG mode of django. Use at own risk.
Please remember to change SECRET_KEY, ALLOWED_HOSTS and DEBUG in settings.py at least.




INSTALL:

Python 3.10+ required.
 
pip packages required:
 - django
 - schedule (used for replication scheduling)
 - ping3 (used for ICMP remote host probes)
 
Please make sure all this present on system.

If you want to install on remote server, there is deploy.sh script, which will copy all files to remote server using SCP.






