
"""base functions"""


def run_command(cmdstring):
	"""run command using subprocess"""
	import subprocess
	import shlex
	
	if len(cmdstring) == 0:
		return -1
	args = shlex.split(cmdstring)
	run_proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	result = subprocess.Popen.communicate(run_proc)[0].decode("utf-8")
	return result


def run_command_with_returncode(cmdstring):
	"""run command using subprocess, return tuple (cmd_output, returncode)"""
	import subprocess
	import shlex
	
	if len(cmdstring) == 0:
		return -1
	args = shlex.split(cmdstring)
	run_proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	result = subprocess.Popen.communicate(run_proc)[0].decode("utf-8")
	return result, run_proc.returncode
	