'''
	Script that finds specific keywords in a transcript and extracts the audio 
	and text starting a certain time before and after the line containing the 
	keyword. The line containing the keyword is uppercased.
	Additionally, the audio and text are in CA format and are automatically 
	linked so that they can be played together.

	To install all dependancies run the following commands with the given
	requirements.txt file:

	1. sudo easy_install pip 
	2. pip install -r requirements.txt
	3. pip install progressbar

'''


from pydub import AudioSegment
from pydub.utils import make_chunks
import argparse   
import os
import sys
import json
import io
import re
from termcolor import colored
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    AdaptiveETA, FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer, UnknownLength

# List of special delimiters in the CA/CHAT formats.
# Used when searching for keywords to ensure that these characters do not
# obstruct finding the keyword if they occur next to it.
SP = [u'\x40',u'\x3a',u'\x2a',u'\x09',u'\x2e','\u02cc',u'\x3f','\u0294',
		u'\x21',u'\x23','\uFF01','\u2248',u'\x3c',u'\x3e','\u25B2','\u2581',
		'\u2193','\u25C1','\u2594','\u2191','\u25c9','\u0332','\u27B4',
		'\u27B6',u'\x28',u'\x29',u'\x5b',u'\x5d','\u222C',u'\xB0',u'\x78',
		u'\x5E','\u263A',u'\xA3','\u2207','\u2206','\u230B','\u230A','\u2309',
		'\u2308','\u204E',u'\x20','\u230a','\u25c1','\u27b4','\u222c',
		'\xb0',u'\x5e','\u263a',u'\xa3','\u230b']

# Function that verifies that the given file exists.
def file_exists(filename):
    if os.path.isfile(filename) == True:
        return True
    else:
        return False

# Function that reads the json file.
def read_json(filename):
	with open(filename, 'r') as f:
	    config= json.load(f)
	    return config

# Function that checks the file extension
def check_extension(filename,extension):
	if filename[filename.rfind('.')+1:] == extension:
		return True
	else:
		return False

# Function that searches for keywords in the file and returns all lines
# with those keywords.
# The mode defines how they keyword should occur in the line i.e. if it is 
# the entire line or part of a line
# Current modes: 1. solo (keyword is alone in line)
#				 2. in_line (keyword is not alone in line)
def search_keywords(all_lines,keywords,form,mode):
	found_lines = []
	ind_lines = []

	# Converting keywords into a dictionary form for statistics
	keywords_dict = dict(zip(keywords,[0] * len(keywords)))

	if form == '.ca' or form == '.cha':
		for word in keywords:
			#print("Keyword: {}".format(word))
			line_num = 0
			for line in all_lines:
				if word in line or word.lower() in line.lower():

					# Changing to lowercase for comparisson
					orig_line = line
					orig_word = word
					line = line.lower()
					word = word.lower()

					if (not line[line.find(word)-1].encode('raw_unicode_escape') in SP):
						line_num += 1
						continue
					if (not line[line.find(word)+len(word)].encode('raw_unicode_escape') in SP):
						line_num += 1
						continue


					# Changing back to original case
					line = orig_line
					word = orig_word

					# Checking the word depending on the mode
					if mode == 'solo':
						check_string = line[line.find(':')+1:]
						check_string = ''.join(x for x in check_string if x.isalpha())
						if (len(check_string) != len(word)):
							line_num += 1
							continue

					# Adding to statistics dictionary
					keywords_dict[word] += 1
					ind_lines.append(line)
					# Ensurnig the line contains the start of the turn
					if (line.find(':') == -1):
						curr_count = line_num
						curr_line = line
						while(curr_line.find(':') == -1):
							curr_count -= 1
							curr_line = all_lines[curr_count]
							line = curr_line + line

					# Ensuring the line contains the end of the turn.
					if (line.find('\x15') == -1):
						curr_count = line_num
						curr_line = line
						while(curr_line.find('\x15') == -1):
							curr_count += 1
							curr_line = all_lines[curr_count]
							line = line + curr_line

					found_lines.append(line)
				line_num += 1
	return found_lines,ind_lines,keywords_dict


# Function that extracts times from lines that were found in the transcript
# The second argument in the format of the text file.
def extract_times(found_lines,form):
	times = []
	if form == '.ca' or form == '.cha':
		for line in found_lines:
			line = unicode(line)
			check = line[line.find('\x15'):line.rfind('\x15')]
			if len(check) > 0:
				start_time = check[check.find('\x15')+1:check.find('_')]
				times.append(float(start_time)/1000)
	return times

# Function that extracts the transcript for the given time range
def extract_transcript(all_lines,times,slice_names,ran,audio_duration,form,
	keywords,found_lines,out_dir_name):

	trans_names = []
	if (form == '.ca' or form == '.cha'):
		for start_time,name in zip(times,slice_names):

			low_thresh = (start_time - ran) * 1000
			if (low_thresh < 0 ):
				low_thresh = 0
			high_thresh = (start_time + ran) * 1000
			if (high_thresh > audio_duration * 1000):
				high_thresh = audio_duration * 1000

			orig_low = low_thresh
			orig_high = high_thresh

			# Searching for a time in all_lines
			line_times = extract_times(all_lines,'.ca')

			low_thresh = (takeClosest(low_thresh/1000,line_times) * 1000)
			ol = low_thresh
			if low_thresh > orig_low:
				low_thresh = line_times[line_times.index(low_thresh/1000) - 1] * 1000
				if low_thresh > orig_low:
					low_thresh = ol
			high_thresh =  (takeClosest(high_thresh/1000,line_times) * 1000)
			if high_thresh < orig_high:
				if (line_times.index(high_thresh/1000) + 1) < len(line_times):
					high_thresh = (line_times[line_times.index(high_thresh/1000) + 1] * 1000)

			low_thresh = low_thresh/1000
			high_thresh = high_thresh/1000

			trans = []
			line_num = 0
			for line in all_lines:
				time = extract_times([line],'.ca')

				# #xtracting the appropriate part of the transcript.
				if (len(time) > 0):	
					if time[0] == low_thresh:
						count = line_num + 1
						trans.append(line)

						while(True):
							if (count == len(all_lines)):
								break
							curr_line = all_lines[count]
							time2 = extract_times([curr_line],'.ca')
							if (curr_line in found_lines):
								curr_line = curr_line.upper()
							if (len(time2) > 0):
								if time2[0] == high_thresh:
									trans.append(curr_line)
									break
							trans.append(curr_line)
							count += 1

				line_num += 1

			trans = zero_times(trans)
			file_name = name[:name.rfind(".")] + '.S.ca'
			trans_names.append(file_name)
			file = open(os.path.join(out_dir_name, file_name),'wb')
			file.write(u'@Media:\t'+unicode(name)+u',audio\n')
			comment = "OIR's: "+" ,".join(keywords)
			file.write(u'@Comment:\t'+unicode(comment)+u'\n')
			for line in trans:
				file.write(line.encode('utf-8', 'ignore'))
			file.write(u'@End\r')
			file.close()
	return trans_names

# Function that zeros the bullets for the transcript file relative to the start
# time. This allows audio to be linked with the transcript.
def zero_times(all_lines):
	line_times = extract_times(all_lines,'.ca')
	start_time = line_times[0] * 1000
	count = 0
	new_trans = []
	for lines in all_lines:
		if (lines.find('\x15') != -1):
			line = lines[:lines.find('\x15')]
			time = lines[lines.find('\x15')+1:lines.rfind('\x15')]
			s_time = str(int(time[:time.find('_')]) - start_time)
			s_time = (int(float(s_time)))
			e_time = str(int(time[time.find('_')+1:]) - start_time)
			e_time = e_time = (int(float(e_time)))
			line = line + '\x15'+unicode(s_time)+'_'+unicode(e_time)+'\x15'+'\n'
			new_trans.append(line)
		else:
			new_trans.append(lines)
	return new_trans

# Helper function that finds the closest number in a list to the given number
def takeClosest(num,collection):
   return min(collection,key=lambda x:abs(x-num))

# Function that finds closest with a certain threshold
def takeCloset_threshold(start_time,line_times,ran):
	min_val = start_time - ran

# Function that slices audio +- x seconds from a given time y seconds
# The input time and range should be in seconds.
def slice_audio(audio_file,start_time,ran,all_lines,out_dir_name):
	audio = AudioSegment.from_wav(audio_file)
	low_thresh = (start_time - ran) * 1000
	if (low_thresh < 0 ):
		low_thresh = 0
	high_thresh = (start_time + ran) * 1000
	if (high_thresh > audio.duration_seconds * 1000):
		high_thresh = audio.duration_seconds * 1000

	orig_low = low_thresh
	orig_high = high_thresh

	line_times = extract_times(all_lines,'.ca')

	low_thresh = (takeClosest(low_thresh/1000,line_times) * 1000)
	ol = low_thresh
	if low_thresh > orig_low:
		low_thresh = line_times[line_times.index(low_thresh/1000) - 1] * 1000
		if low_thresh > orig_low:
			low_thresh = ol
	high_thresh =  (takeClosest(high_thresh/1000,line_times) * 1000)
	if high_thresh < orig_high:
		if (line_times.index(high_thresh/1000) + 1) < len(line_times):
			high_thresh = line_times[line_times.index(high_thresh/1000) + 1] * 1000

	print(low_thresh,high_thresh)


	piece = audio[low_thresh:high_thresh]

	high_thresh = int(high_thresh)
	low_thresh = int(low_thresh)

	piece_name = audio_file[0:audio_file.rfind('.')] + "-"+ str(int(low_thresh)) +"-" + str(int(high_thresh)) + ".wav"
	piece.export(os.path.join(out_dir_name,piece_name), format="wav")
	return piece_name,audio.duration_seconds


# Function that removes all the times which overlap to within a certain 
# threshold so as not to generate redundant transcripts.
def rem_redundant_times(times,thresh):
	rem_times = []
	#print(times)
	new_times = []
	while(True):
		if (len(times) == 0):
			break
		curr_time = times[0]
		if not (curr_time in rem_times):
			new_times.append(curr_time)
			for time in times:
				if abs(float(time) - float(curr_time)) == 0:
					continue
				elif abs(float(time) - float(curr_time)) > thresh:
					new_times.append(time)
					#print("new_time {}".format(new_times))
				elif abs(float(time) - float(curr_time)) <= thresh:
					rem_times.append(time)
					#print("rem_time {}".format(rem_times))
					if (time in new_times):
						new_times.remove(time)
			for time in rem_times:
				times.remove(time)
				rem_times = []
		times.pop(0)
		#print("time {}".format(times))
	#print(new_times)
	final = []
	for i in new_times:
		if i not in final:
			final.append(i)
	return final

# Function that prints output prompt
# Prints statistics for the keywords found.
def output_prompt(slice_names,trans_names,found_lines,keywords,keywords_dict,
	num_turns_total):
	print(colored("\nGailbot Extraction Tool\n"
		"Powered by: Human Interaction Lab - Tufts University\n",'red'))
	print("Keywords Specified: {}\n".format(" ,".join(keywords)))
	print("The following turns in the transcript included the specified keywords...\n")
	for line in found_lines:
		print(line + "\n")
	print("The following audio and transcript slices have been extracted...\n")
	for s_name,t_name in zip(slice_names,trans_names):
		print("\tTranscript file: {}".format(t_name))
		print('\tAudio file: {}\n'.format(s_name))
	print("Basic statistics...\n")
	print('\tTotal number of transcripts generated: {}'.format(len(trans_names)))
	print('\tTotal number of audio files generated: {}'.format(len(slice_names)))
	print('\tTotal number of turns in the transcript: {}'.format(num_turns_total))
	print('\tTotal number of turns with specified keywords: {}'.
		format(len(found_lines)))
	percentage_found = round((float(len(found_lines))/float(num_turns_total))*100,3)
	print('\tHit-rate for keywords in transcript: {}%'.format(percentage_found))
	for word in keywords:
		print("\tNumber of turns containing {}: {}".
			format(word,keywords_dict[word]))
	print(colored("\nThank you for using",'red'))
	print(colored("Gailbot Extraction Tool\n"
		"Powered by: Human Interaction Lab - Tufts University\n",'red'))

if __name__ == '__main__':
	
	# Parsing the input arguments
	parser = argparse.ArgumentParser(
		description = "Client to extract audio and text for specific OIR's in" 
				" a transcript")
	parser.add_argument(
		'-transcript', action = 'store', dest = 'trans_file', required = True)
	parser.add_argument(
		'-config', action = 'store', dest = 'config_file', required = True)
	parser.add_argument(
		'-audio', action = 'store', dest = 'audio_file', required = True)
	args = parser.parse_args()


	# Checking if the files exist
	if (not file_exists(args.trans_file) or 
		not file_exists(args.config_file) or 
		not file_exists(args.audio_file)):
		print("File does not exist\nExiting...")
		sys.exit()

	# Checking the correct file extensions
	if ( not check_extension(args.trans_file,'ca')):
		print('ERROR: Check .ca file extension\nExiting...')
		sys.exit()
	if ( not check_extension(args.config_file,'json')):
		print('ERROR: Check .json file extension\nExiting...')
		sys.exit()
	if ( not check_extension(args.audio_file,'wav')):
		print('ERROR: Check .wav file extension\nExiting...')
		sys.exit()

	# Getting the configuration for the OIR search
	configs = read_json(args.config_file)
	keywords = configs[0]["OIRs"]
	time_thresh = configs[0]["time_thresh"]
	extraction_mode = configs[0]['extraction_mode'].lower()

	# Ensuring we have the correct extraction mode
	if extraction_mode.lower() != "solo" and extraction_mode.lower() != 'in_line':
		print("ERROR: Incorrect extraction mode specified\nExiting...")
		sys.exit()

	if (len(keywords) == 0):
		print("ERROR: No keywords specified\nExiting...")
		sys.exit()
	if (time_thresh < 0):
		print("ERROR: Negative time closeness threshold specified\nExiting...")
		sys.exit()

	# Reading the transcript file into a list of strings.
	txt_file = io.open(args.trans_file, "r",encoding="utf-8")
	all_lines = txt_file.readlines()
	if (all_lines == None):
		print("ERROR: File is empty\nExiting...")
		sys.exit()

	# Searching keywords in the file
	# Last argument is the mode. Must be either solo for keyword to be alone in
	# the turn or in_line for keyword to be present in bigger TCU.
	found_lines,ind_lines, keywords_dict = search_keywords(all_lines,keywords,
		args.trans_file[args.trans_file.rfind('.'):],extraction_mode)
	if (found_lines == None):
		print("ERROR: No OIR's found in file\nExiting...")
		sys.exit()

	# Extracting times for the keywords found
	times = extract_times(found_lines,
		args.trans_file[args.trans_file.rfind('.'):])

	# Only extract timing details are found.
	if (len(times) > 0):
		# Removing times from list that are close to each other (as defined 
		# in the configurations to avoid redundant audio and transcript extractions)
		times = rem_redundant_times(times,time_thresh)
		print(times)

		# Generating output directory name
		out_dir_name = args.audio_file[:args.audio_file.rfind('.')] +'-results'
		if not os.path.exists(out_dir_name):
			os.makedirs(out_dir_name)

		# Extracting audio for all the times and getting the names of all slices
		slice_names = []
		widgets = ['Slicing Audio: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
			' ', ETA(), ' ', FileTransferSpeed()]
		pbar = ProgressBar(widgets=widgets, maxval=10000000)
		print('\n')
		for time in pbar(times):
			name,audio_duration = slice_audio(args.audio_file,time,
				configs[0]['time_range'],all_lines,out_dir_name)
			slice_names.append(name)

		# Extracting the transcript for all the audio chunks
		trans_names = extract_transcript(all_lines,times,slice_names,configs[0]['time_range'],
			audio_duration,args.trans_file[args.trans_file.rfind('.'):],
			keywords,ind_lines,out_dir_name)
	else:
		slice_names = []
		trans_names = []


	# Printing the output prompt and extraction information.
	output_prompt(slice_names,trans_names,found_lines,keywords,keywords_dict,
		len(all_lines))

