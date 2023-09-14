#!/bin/bash
# 
# deploy dfrsync app on remote server
# 

if [ -z "$1" ]
then
	echo "please specify remote local path, or remote path like target-server:/path/to/target/dir as argument"
	exit 1
fi

echo "will deploy dfrsync app to $1"
for f in "dfrsync" "dfrsync.service" "LICENSE" "manage.py" "README.md" "replicator" "start_server.sh"
do
	echo -n "copying $f... "
	scp -r "./$f" "$1"
	echo " done."
done


