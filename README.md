dfrsync

Web App for rsync file replication, scheduled or on-demand.










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
 - [ ] auto-cancell replication task if there is more than N tasks of this type already running
 - [ ] show app log
 - [ ] task runner - show when started and when finished, how long took
 - [ ] redesign page header
 - [ ] post-replication and pre-replication command
 - [x] ensure size of command output log is suffucient
 - [ ] check/validate replication src and dest
 - [ ] check/validate replication options
 - [ ] redesign list of replications
 - [ ] fix non-zero return code of rsync command not threated as error
 - [ ] use one form for add and edit replication
 - [ ] add returncode to ReplicationTask model
 - [ ] start_server.sh runs in background
 - [ ] add stop_server.sh
 - [ ] add authorisation via login/password
 - [ ] add INSTALLATION section to README.md




SECURITY:



This app works in DEBUG mode of django. Use at own risk.
Please remember to change SECRET_KEY and DEBUG in settings.py at least.




