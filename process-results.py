#!/usr/bin/env python3

import math
import os
import re

from pathlib import Path
from datetime import datetime, timedelta
from statistics import mean, stdev, median, quantiles

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BENCH_DIR = Path(SCRIPT_DIR)
DAT_DIR = Path(SCRIPT_DIR) / Path("data")

def time_to_generate(nfs):
	_nfs = nfs['nfs']
	_out_table = nfs['out_table']
	_out_dat_boxplot = nfs['out_dat_boxplot']
	_out_dat_histogram = nfs['out_dat_histogram']
	
	data = {}
	table_data = {}
	data_boxplot = {}

	all_nfs_names = [ nf['name'] for nf in _nfs ]

	for nf in _nfs:
		name = nf['name']
		_in = nf['in']

		with open(_in) as f:
			lines = f.readlines()
			parsed_data = []

			for line in lines:
				if 'time' in line: continue

				line = line.rstrip()
				if not line: continue

				line = re.split(' +|,+', line)

				t = datetime.strptime(line[1],"%H:%M:%S.%f")
				delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

				parsed_data.append(int(delta.total_seconds()))

		m = mean(parsed_data)
		std_dev = stdev(parsed_data)
		_min = min(parsed_data)
		_max = max(parsed_data)
		q = quantiles(parsed_data)

		# lets assume the times are always < 1h
		def get_fmt(t):
			fmt = str(timedelta(seconds=t)).split(".")[0]
			hours = fmt.split(':')[0]
			assert(int(hours) == 0)
			return ':'.join(fmt.split(':')[1:])

		table_data[name] = [ get_fmt(t) for t in [m, std_dev] + q ]
		data_boxplot[name] = [ _min ] + q + [ _max ]
		data[name] = [ m, std_dev ]
	
	table = ''

	table += '\\begin{table}[t]\n'
	table += '\t\\centering\n'
	table += '\t\\resizebox{\\linewidth}{!}{%\n'
	table += '\t\t\\begin{tabular}{l|c|c|c|c|c|}\n'
	table += '\t\t\t\\hline\n'
	table += '\t\t\t\\multicolumn{1}{|l|}{\\textbf{NF}} & \\textbf{Mean} & \\textbf{Std dev} & $\\pmb{P_{25}}$ & $\\pmb{P_{50}}$ & $\\pmb{P_{75}}$ \\\\ \n'
	table += '\t\t\t\\hline\n'
	table += '\t\t\t\\hline\n'

	pre_entry = '\t\t\t\\multicolumn{1}{|l|}'
	post_entry = ' \\\\ \\hline'
	str_if_locks = ' \\textsuperscript{*}'

	for nf in all_nfs_names:
		table += f"{pre_entry}{{{nf}{ str_if_locks if nf in [ 'DBridge', 'LB'] else '' }}} & {' & '.join(table_data[nf])}{post_entry}\n"

	table += '\t\t\t\\multicolumn{6}{l}{\\textsuperscript{*}\\footnotesize{Lock-based implementation.}}\n'
	table += '\t\t\\end{tabular}%\n'
	table += '\t}\n'
	table += '\t\\vspace{-1em}\n'
	table += '\t\\caption{Mean time (mm:ss) to generate each parallel implementation for each NF, with the corresponding standard deviations and quartiles. These values were calculated using 10 generation time samples for each NF.}\n'
	table += '\t\\label{tab:microbenchmarks}\n'
	table += '\t\\vspace{1em}\n'
	table += '\\end{table}\n'

	with open(_out_table, 'w') as o:
		o.write(table)
	
	with open(_out_dat_boxplot, 'w') as o:
		zipped = list(zip(*[ [ nf ] + times for nf,times in data_boxplot.items() ]))
		o.write(f'# {" ".join(zipped[0])}\n')
		for row in zipped[1:]:
			integers = [ str(i) for i in row ]
			o.write(f'{" ".join(integers)}\n')
		
	with open(_out_dat_histogram, 'w') as o:
		for i, (nf, times) in enumerate(data.items()):
			numbers = [ str(t) for t in times ]
			row = ' '.join(numbers)
			o.write(f'{nf} {row} {i}\n')
	
def churn(nfs):
	for nf in nfs:
		data = {}

		with open(nf['infile']) as f:
			lines = f.readlines()
			parsed_data = []

			for line in lines:
				if '#' in line: continue

				line = line.rstrip()
				line = re.split(' +|,+', line)

				line_data = [ int(d) if '.' not in d else float(d) for d in line ]
				if len(line_data) == 4:
					line_data = line_data[0:2] + [0] + line_data[2:]
				parsed_data.append(line_data)

			data_per_cores = {}

			for d in parsed_data:
				fpm   = d[0]
				cores = d[1]
				i     = d[2]
				Gbps  = d[3]
				Mpps  = d[4]

				if cores not in data_per_cores:
					data_per_cores[cores] = {}

				if fpm not in data_per_cores[cores]:
					data_per_cores[cores][fpm] = []

				data_per_cores[cores][fpm].append((Gbps, Mpps))

			for cores in data_per_cores.keys():
				data[cores] = []

				for fpm, values in data_per_cores[cores].items():
					Gbps = [ x[0] for x in values ]
					Mpps = [ x[1] for x in values ]

					if len(Gbps) > 1:
						Gbps_mean = mean(Gbps)
						Gbps_std_dev = stdev(Gbps)

						Mpps_mean = mean(Mpps)
						Mpps_std_dev = stdev(Mpps)
					else:
						Gbps_mean = Gbps[0]
						Gbps_std_dev = 0

						Mpps_mean = Mpps[0]
						Mpps_std_dev = 0
					
					base_Gbps    = 60
					real_fpm     = int(Gbps_mean * fpm / base_Gbps)
					real_fpm_err = int(Gbps_std_dev * fpm / base_Gbps)

					if Gbps_mean < 1:
						continue

					if nf['name'] == 'churn-locks-fw':
						if cores == 1:
							print(f'{fpm:10,} {real_fpm:10,} {Mpps_mean}')
					
					if nf['name'] == 'churn-locks-fw':
						if (cores == 6 and fpm == 1500000) or (cores == 1 and fpm == 2600000):
							continue


					data[cores].append((Gbps_mean, Gbps_std_dev, Mpps_mean, Mpps_std_dev, real_fpm, real_fpm_err))

		for cores, dat in data.items():
			outfile = f"{nf['dat'].split('.')[0]}_cores_{cores}.{nf['dat'].split('.')[1]}"
			assert(len(outfile))

			with open(outfile, 'w') as o:
				for d in dat:
					o.write("{} {} {} {} {} {}\n".format(d[0], d[1], d[2], d[3], d[4] if d[4] != 0 else 500, d[5]))


def skew(nfs):
	data = {}
	for nf in nfs:
		nf_data = []

		with open(nf['infile']) as f:
			lines = f.readlines()
			lines = lines[1:] # skip first line
			parsed_data = []

			for line in lines:
				line = line.rstrip()
				line = re.split(' +|,+', line)

				line_data = [ int(d) if '.' not in d else float(d) for d in line ]
				parsed_data.append(line_data)

			current_cores = -1
			trimmed_data = []

			for d in parsed_data:
				i     = d[0]
				cores = d[1]
				Gbps  = d[2]
				Mpps  = d[3]

				if cores != current_cores:
					trimmed_data.append([])
					current_cores = cores

				trimmed_data[-1].append(( cores, Gbps, Mpps ))

			nf_data = []
			for d in trimmed_data:
				cores = d[0][0]

				Gbps_m = sum(x[1] for x in d) / len(d)
				Mpps_m = sum(x[2] for x in d) / len(d)

				if len(d) > 1:
					Gbps_std_dev = math.sqrt(sum((x[1] - Gbps_m) ** 2 for x in d) / (len(d) - 1))
					Mpps_std_dev = math.sqrt(sum((x[2] - Mpps_m) ** 2 for x in d) / (len(d) - 1))
				else:
					Gbps_std_dev = 0
					Mpps_std_dev = 0

				nf_data.append((cores, Gbps_m, Gbps_std_dev, Mpps_m, Mpps_std_dev))

		data[nf['name']] = nf_data

	uniform = [ nf for nf in data if "uniform" in nf ]
	unbalanced = [ nf for nf in data if "zipf" in nf and "balanced" not in nf ]
	balanced = [ nf for nf in data if "balanced" in nf ]

	final_data = {}

	uniform_out = [ nf['dat'] for nf in nfs if nf['name'] in uniform ]
	unbalanced_out = [ nf['dat'] for nf in nfs if nf['name'] in unbalanced ]
	balanced_out = [ nf['dat'] for nf in nfs if nf['name'] in balanced ]

	assert(len(set(uniform_out)) == 1)
	assert(len(set(unbalanced_out)) == 1)
	assert(len(set(balanced_out)) == 1)

	final_data = {
		'uniform': {
			'out': uniform_out[0],
			'data': [],
			'names': uniform,
		},
		'unbalanced': {
			'out': unbalanced_out[0],
			'data': [],
			'names': unbalanced,
		},
		'balanced': {
			'out': balanced_out[0],
			'data': [],
			'names': balanced,
		},
	}


	for key in final_data.keys():
		core_data = []
		
		for b in final_data[key]['names']:
			dd = data[b]

			for d in dd:
				found = False
				for entry in core_data:
					if entry[0] == d[0]:
						entry[1][0].append(d[1])
						entry[1][1].append(d[2])
						entry[1][2].append(d[3])
						entry[1][3].append(d[4])
						found = True
						break

				if not found:
					core_data.append((d[0], ([d[1]], [d[2]], [d[3]], [d[4]])))

		for d in core_data:
			core = d[0]

			if len(d[1][0]) > 1:
				Gbps_value = mean(d[1][0])
				Gbps_std = stdev(d[1][0])

				Mpps_value = mean(d[1][2])
				Mpps_std = stdev(d[1][2])
			else:
				Gbps_value = d[1][0][0]
				Gbps_std = 0

				Mpps_value = d[1][2][0]
				Mpps_std = 0

			final_data[key]['data'].append((core, Gbps_value, Gbps_std, Mpps_value, Mpps_std))

	for nf in final_data:
		outfile = final_data[nf]['out']
		dat = final_data[nf]['data']

		with open(outfile, 'w') as o:
			for cores, Gbps_value, Gbps_std, Mpps_value, Mpps_std in dat:
				o.write("{} {} {}\n".format(cores, Mpps_value, Mpps_std))

def technologies(nfs):
	data = {}

	for nf in nfs:
		with open(nf['infile']) as f:
			lines = f.readlines()
			lines = lines[1:] # skip first line
			
			parsed_data = []
			for line in lines:
				line = line.rstrip()
				line = line.split(',')

				line_data = [ int(d) if '.' not in d else float(d) for d in line ]
				parsed_data.append(line_data)

			cores = -1
			trimmed_data = []
			for d in parsed_data:
				_i = d[0]
				_cores = d[1]
				_gbps = d[2]
				_mpps = d[3]

				if _cores != cores:
					trimmed_data.append([])
					cores = _cores

				# cores, Gbps and Mpps
				trimmed_data[-1].append([ _cores, _gbps, _mpps ])

			nf_data = []
			for d in trimmed_data:
				cores = d[0][0]

				# grabbing Gbps
				# _median = median(x[1] for x in d)

				# m = min(x[1] for x in d)
				# M = max(x[1] for x in d)

				# grabbing Mpps
				_median = median(x[2] for x in d)

				m = min(x[2] for x in d)
				M = max(x[2] for x in d)

				nf_data.append((cores, _median, m, M))
			
			# base = [ e for e in nf_data if e[0] == 1  ]
			# assert len(base) == 1
			# base_perf_mpps = base[0][1]

			# for i, d in enumerate(nf_data):
			# 	speedup = d[1] / base_perf_mpps
			# 	nf_data[i] = d + (speedup,)

		data[nf['name']] = nf_data

	for nf in data:
		outfile = ''
		for _nf in nfs:
			if _nf['name'] == nf:
				outfile = _nf['dat']
				break
		assert(len(outfile))

		with open(outfile, 'a') as o:
			for d in data[nf]:
				cores, _median, minimum, maximum = d
				o.write("\"{}\" {} {} {}\n".format(nf, _median, minimum, maximum))


def technologies_gbps(nfs):
	data = {}

	for nf in nfs:
		with open(nf['infile']) as f:
			lines = f.readlines()
			lines = lines[1:] # skip first line
			
			parsed_data = []
			for line in lines:
				line = line.rstrip()
				line = line.split(',')

				line_data = [ int(d) if '.' not in d else float(d) for d in line ]
				parsed_data.append(line_data)

			cores = -1
			trimmed_data = []
			for d in parsed_data:
				_i = d[0]
				_cores = d[1]
				_gbps = d[2]
				_mpps = d[3]

				if _cores != cores:
					trimmed_data.append([])
					cores = _cores

				# cores, Gbps and Mpps
				trimmed_data[-1].append([ _cores, _gbps, _mpps ])

			nf_data = []
			for d in trimmed_data:
				cores = d[0][0]

				# grabbing Gbps
				_median = median(x[1] for x in d)

				m = min(x[1] for x in d)
				M = max(x[1] for x in d)

				# grabbing Mpps
				#_median = median(x[2] for x in d)

				#m = min(x[2] for x in d)
				#M = max(x[2] for x in d)

				nf_data.append((cores, _median, m, M))
			
			# base = [ e for e in nf_data if e[0] == 1  ]
			# assert len(base) == 1
			# base_perf_mpps = base[0][1]

			# for i, d in enumerate(nf_data):
			# 	speedup = d[1] / base_perf_mpps
			# 	nf_data[i] = d + (speedup,)

		data[nf['name']] = nf_data

	for nf in data:
		outfile = ''
		for _nf in nfs:
			if _nf['name'] == nf:
				outfile = _nf['dat']
				break
		assert(len(outfile))

		with open(outfile, 'a') as o:
			for d in data[nf]:
				cores, _median, minimum, maximum = d
				o.write("\"{}\" {} {} {}\n".format(nf, _median, minimum, maximum))

def loc(nfs):
	data = {}

	for nf in nfs:
		with open(nf['infile']) as f:
			lines = f.readlines()
			lines = lines[1:] # skip first line
			
			parsed_data = []
			for line in lines:
				line = line.rstrip()
				line = line.split(',')

				line_data = [ str(d) for d in line ]
				parsed_data.append(line_data)

			trimmed_data = []
			_total = 0
			for d in parsed_data:
				_files = d[0]
				_lang = d[1]
				_blank = d[2]
				_comment = d[3]
				_code = d[4]

				# files, code only from C files
				if _lang == "C" or _lang == "C/C++ Header":
					_total = _total + int(_code) + int(_blank) + int(_comment)

			trimmed_data.append([ _total ])

			nf_data = []
			for d in trimmed_data:
				nf_data.append((d[0]))

		data[nf['name']] = nf_data

	for nf in data:
		outfile = ''
		for _nf in nfs:
			if _nf['name'] == nf:
				outfile = _nf['dat']
				break
		assert(len(outfile))

		with open(outfile, 'a') as o:
			for d in data[nf]:
				lines = d
				o.write("\"{}\" {}\n".format(nf, lines))



def packet_size(nfs):
	assert(len(nfs) == 1)
	nf = nfs[0]

	nf_data = []

	with open(nf['infile']) as f:
		lines = f.readlines()
		parsed_data = []

		for line in lines:
			if '#' in line: continue

			line = line.rstrip()
			line = re.split(' +|,+', line)

			line_data = line
			line_data = [ int(d) if d.isnumeric() else d for d in line_data ]
			line_data = [ float(d) if type(d) == str and '.' in d else d for d in line_data ]
			parsed_data.append(line_data)

		merged_data = []

		for d in parsed_data:
			pkt_sz  = d[0]
			i       = d[1]
			Gbps    = d[2]
			Mpps    = d[3]

			filtered = list(filter(lambda d: d[0] == pkt_sz, merged_data))

			if len(filtered):
				filtered[0][1].append(Gbps)
				filtered[0][1].append(Mpps)
			else:
				merged_data.append((pkt_sz, [ Gbps ], [ Mpps ]))

		for d in merged_data:
			pkt_sz   = d[0]
			all_Gbps = d[1]
			all_Mpps = d[2]

			if pkt_sz == 'internet':
				pkt_sz = '\"Internet\"'

			if len(all_Gbps) > 1:
				Gbps_mean = mean(all_Gbps)
				Gbps_std = stdev(all_Gbps)

				Mpps_mean = mean(all_Mpps)
				Mpps_std = stdev(all_Mpps)
			else:
				Gbps_mean = all_Gbps[0]
				Gbps_std = 0

				Mpps_mean = all_Mpps[0]
				Mpps_std = 0

			nf_data.append((pkt_sz, Gbps_mean, Gbps_std, Mpps_mean, Mpps_std))

	nf_data.sort(key=lambda tup: tup[1])
	outfile = nf['dat']
	with open(outfile, 'a') as o:
		for d in nf_data:
			o.write("{} {} {} {} {}\n".format(d[0], d[1], d[2], d[3], d[4]))

def latency_cdf(nfs):
	for nf in nfs:
		samples = []

		with open(nf['infile']) as f:
			lines = f.readlines()

			for line in lines:
				sample_ns = int(line.rstrip())
				samples.append(sample_ns)
		
		# minimum = min(samples)
		maximum = max(samples)

		step_unit_ns = 1000

		cdf = []

		boundary = 0
		while True:
			filtered = list(filter(lambda sample_ns: sample_ns <= boundary, samples))
			probability = len(filtered) / len(samples)

			cdf.append((boundary, probability))

			if boundary == maximum:
				break

			boundary += step_unit_ns

			if boundary > maximum:
				boundary = maximum

		outfile = nf['dat']
		with open(outfile, 'w') as o:
			for boundary_ns, probability in cdf:
				boundary_us = int(boundary_ns / 1000)
				o.write("{} {}\n".format(boundary_us, probability))

lut = [
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_64B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128.dat',
			},
		] 
	},
		{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_128B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_128_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256.dat',
			},
		] 
	},
		{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_256B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_256_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512.dat',
			},
		] 
	},
		{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_512B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_512_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024.dat',
			},
		] 
	},
		{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1024B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1024_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500.dat',
			},
		] 
	},
		{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_1500B_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_1500_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_internet_throughput.csv',
				'dat': f'{DAT_DIR}/throughput_uni_internet_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_128B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_128B_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_256B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_256B_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_512B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_512B_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B.dat',
			},
		] 
	},
		{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_1024B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1024B_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_1500B.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_1500B_gbps.dat',
			},
		] 
	},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet.dat',
			},
		] 
	},
	{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_uniform_internet.csv',
				'dat': f'{DAT_DIR}/hm_throughput_uni_internet_gbps.dat',
			},
		] 
	},
	{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B.dat',
        },
    ] 
	},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-64B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-128B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_128B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-256B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_256B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-512B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_512B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1024B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1024B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-1500B_throughput.csv',
            'dat': f'{DAT_DIR}/throughput_zipf_1500B_gbps.dat',
        },
    ] 
},
	{
		'processor': technologies,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf.dat',
			},
		] 
	},
	{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B.dat',
        },
    ] 
},
{
    'processor': technologies,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B.dat',
        },
    ] 
},
{
		'processor': technologies_gbps,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf_gbps.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf_gbps.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf_gbps.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf.csv',
				'dat': f'{DAT_DIR}/hm_throughput_zipf_gbps.dat',
			},
		] 
	},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-128B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_128B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-256B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_256B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-512B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_512B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-1024B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1024B_gbps.dat',
        },
    ] 
},
{
    'processor': technologies_gbps,
    'nfs': [
        {
            'name': 'fw+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_up_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B_gbps.dat',
        },
        {
            'name': 'fw+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_fw_pol_down_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B_gbps.dat',
        },
        {
            'name': 'nat+polup',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_up_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B_gbps.dat',
        },
        {
            'name': 'nat+poldown',
            'infile': f'{BENCH_DIR}/throughput/hm_nat_pol_down_throughput_zipf-1500B.csv',
            'dat': f'{DAT_DIR}/hm_throughput_zipf_1500B_gbps.dat',
        },
    ] 
},

	{
		'processor': loc,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/loc/fw_wan_1_pol_wan_0_lan_1_config_bdd1_cloc_tool.csv',
				'dat': f'{DAT_DIR}/loc_tool.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/loc/fw_wan_1_pol_wan_1_lan_0_config_bdd1_cloc_tool.csv',
				'dat': f'{DAT_DIR}/loc_tool.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/loc/nat_wan_1_pol_wan_0_lan_1_config_bdd1_cloc_tool.csv',
				'dat': f'{DAT_DIR}/loc_tool.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/loc/nat_wan_1_pol_wan_1_lan_0_config_bdd1_cloc_tool.csv',
				'dat': f'{DAT_DIR}/loc_tool.dat',
			},
		] 
	},
	{
		'processor': loc,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/loc/fw_pol_up_cloc_hm.csv',
				'dat': f'{DAT_DIR}/loc_hm.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/loc/fw_pol_down_cloc_hm.csv',
				'dat': f'{DAT_DIR}/loc_hm.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/loc/nat_pol_up_cloc_hm.csv',
				'dat': f'{DAT_DIR}/loc_hm.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/loc/nat_pol_down_cloc_hm.csv',
				'dat': f'{DAT_DIR}/loc_hm.dat',
			},
		] 
	},
	{	
		'processor': latency_cdf,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/latency/fw_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_fw_polup_latency_uni.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/latency/fw_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_fw_poldown_latency_uni.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/latency/nat_wan_1_pol_wan_0_lan_1_config_bdd1_uniform_64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_nat_polup_latency_uni.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/latency/nat_wan_1_pol_wan_1_lan_0_config_bdd1_uniform_64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_nat_poldown_latency_uni.dat',
			},
		] 
	},
	{	
		'processor': latency_cdf,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/latency/fw_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_fw_polup_latency_zipf.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/latency/fw_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_fw_poldown_latency_zipf.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/latency/nat_wan_1_pol_wan_0_lan_1_config_bdd1_zipf-64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_nat_polup_latency_zipf.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/latency/nat_wan_1_pol_wan_1_lan_0_config_bdd1_zipf-64B_latency.csv',
				'dat': f'{DAT_DIR}/tool_nat_poldown_latency_zipf.dat',
			},
		] 
	},
	{	
		'processor': latency_cdf,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/latency/hm_fw_pol_up_latency_zipf.csv',
				'dat': f'{DAT_DIR}/hm_fw_polup_latency_zipf.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/latency/hm_fw_pol_down_latency_zipf.csv',
				'dat': f'{DAT_DIR}/hm_fw_poldown_latency_zipf.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/latency/hm_nat_pol_up_latency_zipf.csv',
				'dat': f'{DAT_DIR}/hm_nat_polup_latency_zipf.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/latency/hm_nat_pol_down_latency_zipf.csv',
				'dat': f'{DAT_DIR}/hm_nat_poldown_latency_zipf.dat',
			},
		] 
	},
	{	
		'processor': latency_cdf,
		'nfs': [
			{
				'name': 'fw+polup',
				'infile': f'{BENCH_DIR}/latency/hm_fw_pol_up_latency.csv',
				'dat': f'{DAT_DIR}/hm_fw_polup_latency_uni.dat',
			},
            {
				'name': 'fw+poldown',
				'infile': f'{BENCH_DIR}/latency/hm_fw_pol_down_latency.csv',
				'dat': f'{DAT_DIR}/hm_fw_poldown_latency_uni.dat',
			},
            {
				'name': 'nat+polup',
				'infile': f'{BENCH_DIR}/latency/hm_nat_pol_up_latency.csv',
				'dat': f'{DAT_DIR}/hm_nat_polup_latency_uni.dat',
			},
            {
				'name': 'nat+poldown',
				'infile': f'{BENCH_DIR}/latency/hm_nat_pol_down_latency.csv',
				'dat': f'{DAT_DIR}/hm_nat_poldown_latency_uni.dat',
			},
		] 
	}
]

def main():
	if not os.path.exists(DAT_DIR):
		os.mkdir(DAT_DIR)

	for entry in lut:
		entry['processor'](entry['nfs'])

if __name__ == '__main__':
	main()