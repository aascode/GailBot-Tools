from lxml import etree
import os.path
import sys
import os
import argparse
import codecs				# For reading utf-8 files
import subprocess


# Function that verifies that the given file exists.
def file_exists(filename):
    if os.path.isfile(filename) == True:
        return True
    else:
        return False


# Function that checks the file extension
def check_extension(filename,extension):
	if filename[filename.rfind('.')+1:] == extension:
		return True
	else:
		return False

'''
Function that removes specific start and end delimiters from a file stream
Inputs:
	1. all_data -> List containing all lines of CHAT file.
	2. start_delim_list -> List of individual characters comprising the starting
		delimiter.
	3. end_delim_list -> List of individual characters comprising the ending
		delimiter.
Returns -> List containing the modified data.
'''
def rem_delim(all_data, start_delim_list, end_delim_list):
	if len(start_delim_list) == 0 or len(end_delim_list) == 0:
		return all_data
	new_data = []
	for line in all_data:
		start_delims = ''.join(start_delim_list)
		end_delims = ''.join(end_delim_list)
		# Verify that the starting delimiters exist
		check_start = line.find(start_delims)
		# Substring after initial delimiters.
		sub_line = line[check_start+len(start_delims):]
		check_end = sub_line.find(end_delims)
		if check_start != -1 and check_end != -1:
			# Removing the delimiters if both starting and ending pairs are 
			# found.
			check_end += check_start+len(start_delims)
			sub_str = (line[:check_start] + 
				line[check_start + len(start_delims):check_end] +
				line[check_end + len(end_delims):])
			new_data.append(sub_str)
		else:
			new_data.append(line)
	# New list with the modified lines returned
	return new_data

# Function that fixes the bullets if start time > end time
# Input -> List containing all the lines.
# Output -> Modified list with fixed bullets.
def fix_bullets(all_data):
	for i,line in enumerate(all_data):
		start_bullet_pos = line.find('\x15')+1
		end_bullet_pos = line.rfind('\x15')
		if start_bullet_pos != -1 and end_bullet_pos != -1:
			times = line[start_bullet_pos:end_bullet_pos]
			start_time = times[:times.find('_')]
			end_time = times[times.find('_')+1:end_bullet_pos]
			if int(start_time) > int(end_time):
				new_times = end_time + "_" + start_time
				newline = line[:start_bullet_pos] + new_times + line[end_bullet_pos:]
				all_data[i] = newline
	return all_data

# Function that removes the negative sign from a line
# Input -> List containing all the lines.
# Output -> Modified list with the removed negative sign.
def fix_neg_sign(all_data):
	for i, line in enumerate(all_data):
		if line[0] != '@':
			line = line.replace('-','')
		all_data[i] = line
	return all_data


# Functions that ensures that only valid periods exist in a line.
# Input -> List of all the lines
# Output -> Modified list of all the lines
def check_periods(all_data):
	new_data = []
	for i, line in enumerate(all_data):
		for j,char in enumerate(line):
			if char == '.':
				if line[j-1].isalpha():
					for i in range(line.count('.')-1):
						line = line[:j] + line[j+1:]
						j+=2
		new_data.append(line)
	return new_data

def rem_lone_delimiter(all_data,delim_list):
	delim = ''.join(delim_list)
	new_data = []
	for line in all_data:
		pos = line.find(delim)
		if pos != -1:
			if line[pos-1] == ' ' and line[pos+1] == ' ':
				#print('NEW')
				#print(line)
				line = line[:pos] + line[pos+1:]
				#print(line)
		new_data.append(line)
	return new_data



# Function that removes unnecessary lines and fixes syntax in the CHAT file.
# Input -> List containing the lines
# Output -> List containing the modified lines.
def refine_CHAT(all_data):
	# Removing the comment markers.
	new_data = rem_delim(all_data,['[','^'],[']'])
	new_data = [line.replace('%','') for line in new_data]
	# Removing **** that indicate curse words.
	new_data = [line.replace('****','CURSE') for line in new_data]
	# Removing any negative times in the transcript.
	new_data = fix_neg_sign(new_data)
	# Fixing the bullet markers
	new_data = fix_bullets(new_data)
	# Fixing the extra periods in the sentence
	new_data = check_periods(new_data)
	# Removing empty comment markers
	new_data = [line.replace('[^','') for line in new_data]
	# Removing lone delimiters ( ']' marker here)
	new_data = rem_lone_delimiter(new_data,']')
	return new_data

# Function that gets the line numbers from the CHATTER output.
# Inputs -> Output of the Chatter script run on the file.
# Outputs -> List of numbers indicating the lines to be removed.
def get_line_nums(chatter_output):
	line_nums = []
	lines = chatter_output.split('\n')
	for line in lines:
		start_pos = line.find('line')
		if start_pos != -1:
			number = line[start_pos+5:line.find(',')]
			line_nums.append(int(number))
	line_nums = list(set(line_nums))
	line_nums.sort()
	return line_nums


# Function that removes the given lines from the data
# Inputs -> all_data is a list of all lines
#			line_nums is the line numbers to be removed.
#			lines_removed is a list of the lines removed from the file.
# Output -> List containing the modified lines.
def remove_lines(all_data,line_nums,lines_removed):
	new_data = []
	for i, line in enumerate(all_data):
		if line[0] == '@':
			new_data.append(line)
		elif not i in line_nums:
			new_data.append(line)
		else:
			if line.find(':') != -1:
				if line.split('.')[-1].find('\x15') == 1:
					newline = line[:line.find(":")+1] + "\tORIGINAL DATA REMOVED  . " + line[line.find('\x15'):]
				else:
					newline = line[:line.find(":")+1] + "\tORIGINAL DATA REMOVED " + line[line.find('\x15'):]
			else:
				if line.split('.')[-1].find('\x15') == 1:
					newline = "\tORIGINAL DATA REMOVED . " + line[line.find('\x15'):]
				else:
					newline = "\tORIGINAL DATA REMOVED " + line[line.find('\x15'):]
			if line.find("ORIGINAL") == -1:
				new_data.append(newline)
				lines_removed.append([i,line])
	return new_data
	
	
# Function that recursively uses chatter to convert CHAT to XML.
# Input -> String that is the command to run the chatter script.
#			List of the lines
#			Filename of the CHAT file.
# Output -> List of lines that were removed.
def convert(chatter_command,new_data,file):
	with open(file, 'w') as f:
		for item in new_data:
			f.write("%s" % item)
	lines_removed = []
	while True:
		# Calling the chatter command as a subprocess in a shell.
		proc = subprocess.Popen(chatter_command ,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		# Storing the stdout stream from the chatter command.
		chatter_output =  proc.communicate()[0]
		#print(chatter_output)
		# Getting illegal line numbers from the chatter stdout stream.
		line_nums = get_line_nums(chatter_output)
		# Stop if there are no lines to fix.
		if(len(line_nums) == 0):
			break
		# Removing illegal lines from data/
		new_data = remove_lines(new_data,line_nums,lines_removed)
		# Writing the modified data.
		with open(file,'w') as f:
			for line in new_data:
				f.write("%s" % line)
	return lines_removed


# The main run function for the program
# Inputs -> Name of the directory containing the file
#			Filename
def run(file,dir_name = ''):
	# Verifying files
	if (not check_extension(dir_name+file,"cha") or not 
			file_exists(dir_name+file)):
		print("ERROR: Verify .cha file extension and that file exists")
		print("FILENAME: " + file)
		return
	# Reading files in text mode.
	with open(dir_name+file,'rU') as f:
		all_data = f.readlines()
		# Removing illegal syntax from CHAT file.
	new_data = refine_CHAT(all_data)
	# The command to give to Talkbank's CHATTER program.
	chatter_command = 'java -cp chatter.jar org.talkbank.chatter.App' \
	' -inputFormat cha -outputFormat xml ' + dir_name+file + ' >> '+dir_name+file[:file.rfind('.')]+'.xml'
	lines_removed = convert(chatter_command,new_data,dir_name+file)

	# Re-writing the original CHAT file.
	with open(dir_name+file, 'w') as f:
		for item in all_data:
			f.write("%s" % item)
	print('\nFILENAME: ' + file)
	percentage = round((float(len(lines_removed))/float(len(new_data)))*100,4)
	print('The numbers of lines removed is: ' + str(len(lines_removed)) + ' [' + str(percentage) +' % ]')
	print('The following lines were removed\n')
	for line in lines_removed:
		print(line)
	print('\n')
	

if __name__ == '__main__':

	# Parse command line parameters
	parser = argparse.ArgumentParser(
		description = ('client convert CHAT to XML'))
	parser.add_argument('-directory',action = 'store',dest = 'in_direc', nargs=1,
		required = False)
	parser.add_argument(
		'-files', action = 'store', dest = 'in_files', default = None,
		help = 'path to the CHAT file(s)', nargs = '*', required = False)
	args = parser.parse_args()


	# Getting the directory name
	if args.in_direc != None:
		dir_name = "./"+args.in_direc[0]
		# Going through the directory
		for root, dirs, files in os.walk(args.in_direc[0]):
			for file in files:
				run(dir_name = dir_name,file = file)
				
	#G oing through the files.
	if args.in_files != None:
		for file in args.in_files:
			run(file = file)































