#Other vars
BASE_LOG=experiment.log
CURRENT_LOG=$BASE_LOG
USER_HOME=/home/pedromoreira56

#Traffic generator paths
TG=graveler
TG_EVAL_DIR=$USER_HOME/nf-comb-eval
TG_PCAPS_DIR=$TG_EVAL_DIR/pcaps
TG_EVAL_BENCH_DIR=$TG_EVAL_DIR/bench

#DUT Vars
DUT=geodude
DUT_BUNDLE_SCRIPT=$USER_HOME/maestro/dpdk-nfs/synthesized/tools/build_comb.py
DUT_NFCOMB_DIR=$USER_HOME/maestro/dpdk-nfs/nf-comb
DUT_NFS_DIR=$DUT_NFCOMB_DIR/examples
DUT_COMBS_HM_DIR=$DUT_NFCOMB_DIR/examples-handmade
DUT_COMBS_DIR=$DUT_NFCOMB_DIR/examples-comb
DUT_COMBS_CONFIG_DIR=$DUT_NFCOMB_DIR/configs
DUT_EVAL_DIR=$DUT_NFCOMB_DIR
DUT_MAESTRO_PATHS_FILE=$USER_HOME/maestro/build/paths.sh
DUT_SYNTHESIZED_DIR=$USER_HOME/maestro/dpdk-nfs/synthesized/build
DUT_CORES="16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"

#Bench config
CURRENT_RUNNING_NF=""
ITERATIONS=10 #10
ITERATION_DURATION_SEC=5 #5
TG_REPLAY_PCAP_SCRIPT=/opt/snaplab/toolbox/replay-pcap.py
TG_TX_DEV="0000:af:00.0"
TG_RX_DEV="0000:af:00.1"
TG_TX_CORES=6
TG_RX_CORES=6
ADDITIONAL_REPLAY_PCAP_FLAGS=""


download() {
	local host=$1
	local remote_file=$2
	local local_file=$3
	scp -q "$host:$remote_results_file" "$local_results_file"
}

check_folder() {
  if [ ! -d "$1" ]; then
    echo "Error: Folder $1 does not exist."
    exit 1
  fi
}

set_log() {
	local exp_dir=$1
	CURRENT_LOG="$exp_dir/$BASE_LOG"
}

log() {
	local msg=$1
	echo "$msg" >> $CURRENT_LOG
}

ssh_run() {
	local host=$1
	local cmd=$2

	log "[$host] $cmd"
	ssh -q -t $host "$cmd"
}

tg_run() {
	local cmd=$1
	local cwd="${2:-}"

	#cmd="source $TG_ACTIVATE_PYTHON_ENV_SCRIPT; $cmd"

	if [[ ! -z "$cwd" ]]; then
		cmd="cd $cwd; $cmd"
	else
		cmd="cd $TG_EVAL_DIR; $cmd"
	fi

	ssh_run $TG "$cmd"
}

dut_run() {
	local cmd=$1
	local cwd="${2:-}"

	cmd="source $DUT_MAESTRO_PATHS_FILE; $cmd"

	if [[ ! -z "$cwd" ]]; then
		cmd="cd $cwd; $cmd"
	else
		cmd="cd $DUT_EVAL_DIR; $cmd"
	fi

	ssh_run $DUT "$cmd"
}

tg_check_file() {
	file=$1

	if ! tg_run "stat $file >/dev/null 2>&1"; then
		echo "ERROR: $pcap not found in TG. Exiting."
		exit 1
	fi
}

dut_check_file() {
	file=$1

	if ! dut_run "stat $file >/dev/null 2>&1"; then
		echo "ERROR: $pcap not found in DUT. Exiting."
		exit 1
	fi
}

# #TODO cannot merge because build not working
# merge-nfs(){

# 	local nf1_dir=$1
# 	local nf2_dir=$2
# 	local config_file=$3
# 	local merged_dir=$4

# 	dut_run "make bdd > /dev/null 2>&1" "$nf1_dir"
# 	dut_run "make bdd > /dev/null 2>&1" "$nf2_dir"

# 	dut_run "nf-comb -bdd1 $nf1_dir/nf.bdd -bdd2 $nf2_dir/nf.bdd -config $config_file -out $merged_dir/nf > $merged_dir/output 2>&1"

# 	dut_run "bdd-to-c -in $merged_dir/nf.bdd -out $merged_dir/comb.c -target seq > /dev/null 2>&1"

# 	dut_run "$DUT_BUNDLE_SCRIPT $merged_dir/comb.c sequential $nf1_dir $nf2_dir > $merged_dir/output 2>&1"
# }

build_nf() {

	local nf_1=$1
	local nf_2=$2
	local config=$3
	local exp_name=$4

	local nf_path_1="$DUT_NFS_DIR/$nf_1"
	local nf_path_2="$DUT_NFS_DIR/$nf_2"

	local merged_nf="${nf_1}_${nf_2}_${config%.json}"
	local merged_nf_path="examples-comb/$merged_nf"

	dut_run "mkdir -p $DUT_COMBS_DIR"
	dut_run "mkdir -p $merged_nf_path"

	#TODO cannot merge because build not working
	# if ! dut_run "stat nf.c > /dev/null 2>&1" "$merged_nf_path"; then 
	# 	#merge-nfs "$nf_path_1" "$nf_path_2" "$DUT_COMBS_CONFIG_DIR/$config" "$merged_nf_path"
	# fi

	if ! dut_run "stat $merged_nf_path/build/app/nf > /dev/null 2>&1"; then 
		dut_run "cd $merged_nf_path && make > /dev/null 2>&1"
	fi

	echo "$merged_nf_path/build/app/nf"
}

kill_nf() {
	local nf_exe=$1
	dut_run "sudo killall -SIGKILL $nf_exe >/dev/null 2>&1 || true"
}

__setup_bench() {
	local nf_exe=$1
	local tmp_results_file=$2

	log ""
	log "============================================================"
	log ""

	# Kill NF before exiting
	CURRENT_RUNNING_NF="$nf_exe"
	trap 'kill_nf $CURRENT_RUNNING_NF' EXIT

	touch $tmp_results_file
	echo -e "i,#cores,Gbps,Mpps,loss" > $tmp_results_file
}

__finalize_bench() {
	local tmp_results_file=$1
	local results_file=$2

	mv $tmp_results_file $results_file
}

ssh_run_background() {
	local host=$1
	local cmd=$2

	log "[$host] $cmd"
	ssh -q $host "$cmd >/dev/null 2>&1 &"
}

dut_run_background() {
	local cmd=$1
	local cwd="${2:-}"

	cmd="source $DUT_MAESTRO_PATHS_FILE; $cmd"

	if [[ ! -z "$cwd" ]]; then
		cmd="cd $cwd; $cmd"
	else
		cmd="cd $DUT_EVAL_DIR; $cmd"
	fi

	ssh_run_background $DUT "$cmd"
}

run_nf() {
	local nf_exe=$1
	local lcores=$2
	local nf_args="${3:-}"

	if [[ ! -z "$nf_args" ]]; then
		dut_run_background "sudo $nf_exe --lcores $lcores -- $nf_args"
	else
		dut_run_background "sudo $nf_exe --lcores $lcores"
	fi
}

is_prog_running() {
	local host=$1
	local prog=$2
	ssh_run "$host" "pgrep -f -x .*$prog.*" >/dev/null
}

wait_for_nf() {
	local nf_exe=$1

	local max_tries=10
	for (( t=0; t<$max_tries; t++ )); do
		if is_prog_running "$DUT" "$nf_exe"; then
			# Give time to balance LUTs (if needed)
			sleep 3
			return 0
		fi

		sleep 0.5
	done
	
	echo "Max tries exceeded, NF is not running :("
	exit 1
}

replay_pcap() {
	local pcap=$1
	local local_results_file=$2

	if ! tg_run "stat $pcap >/dev/null 2>&1" "$TG_PCAPS_DIR"; then
		echo "ERROR: $TG_PCAPS_DIR/$pcap not found in TG. Exiting."
		exit 1
	fi

	local cmd="$TG_REPLAY_PCAP_SCRIPT"
	cmd="$cmd $TG_TX_DEV $TG_RX_DEV $TG_PCAPS_DIR/$pcap"
	cmd="$cmd --tx-cores $TG_TX_CORES"
	cmd="$cmd --rx-cores $TG_RX_CORES"
	cmd="$cmd --duration $ITERATION_DURATION_SEC"
	cmd="$cmd --find-stable-throughput"
	cmd="$cmd $ADDITIONAL_REPLAY_PCAP_FLAGS"

	tg_run "sudo $cmd" "$TG_EVAL_BENCH_DIR" >> $CURRENT_LOG

	local remote_results_file="$TG_EVAL_BENCH_DIR/results.csv"
	
	download "$TG" "$remote_results_file" "$local_results_file"
	tg_run "rm -f $remote_results_file"
}


replay_pcap_latency() {
	local pcap=$1
	local local_results_file=$2

	local rate=1 # Gbps

	if ! tg_run "stat $pcap >/dev/null 2>&1" "$TG_PCAPS_DIR"; then
		echo "ERROR: $TG_PCAPS_DIR/$pcap not found in TG. Exiting."
		exit 1
	fi

	local cmd="$TG_REPLAY_PCAP_SCRIPT"
	cmd="$cmd $TG_TX_DEV $TG_RX_DEV $TG_PCAPS_DIR/$pcap"
	cmd="$cmd --tx-cores 1"
	cmd="$cmd --rx-cores 1"
	cmd="$cmd --duration $ITERATION_DURATION_SEC"
	cmd="$cmd --latency"
	cmd="$cmd --rate $rate"
	cmd="$cmd $ADDITIONAL_REPLAY_PCAP_FLAGS"

	tg_run "sudo $cmd" "$TG_EVAL_BENCH_DIR" >> $CURRENT_LOG

	local remote_results_file="$TG_EVAL_BENCH_DIR/results.csv"
	
	download "$TG" "$remote_results_file" "$local_results_file"
	tg_run "rm -f $remote_results_file"
}


__run_bench_with_n_cores() {
	local nf_exe=$1
	local pcap=$2
	local n_cores=$3
	local intermediate_results_file=$4
	local tmp_results_file=$5
	local exp_name=$6
	local nf_args="${7:-}"

	local lcores=$(python3 -c "print(','.join('$DUT_CORES'.split(',')[:$n_cores]))")

	echo "[$exp_name] Running NF with $n_cores cores ($lcores)"
	
	if [[ ! -z "$nf_args" ]]; then
		run_nf "$nf_exe" "$lcores" "$nf_args"
	else 
		run_nf "$nf_exe" "$lcores"
	fi

	wait_for_nf "$nf_exe"

	for ((i=1;i<=$ITERATIONS;i++)); do
		echo "[$exp_name]   * Running benchmark {$i/$ITERATIONS, pcap=$pcap}"
		log "NF: $exp_name, cores: $lcores, pcap: $pcap, it: $i/$ITERATIONS"

		replay_pcap "$pcap" "$intermediate_results_file"

		local mpps=$(cat $intermediate_results_file | tail -n 1 | awk -F ',' '{print $1}')
		local gbps=$(cat $intermediate_results_file | tail -n 1 | awk -F ',' '{print $2}')
		local loss=$(cat $intermediate_results_file | tail -n 1 | awk -F ',' '{print $5}')

		echo "[$exp_name]         results: $gbps Gbps $mpps Mpps $loss% loss"
		echo -e "$i,$n_cores,$gbps,$mpps,$loss" >> $tmp_results_file

		rm -f $intermediate_results_file
	done

	echo "[$exp_name]   * Killing NF"
	kill_nf "$nf_exe"
}

__run_bench_with_n_cores_latency() {
	local nf_exe=$1
	local pcap=$2
	local n_cores=$3
	local intermediate_results_file=$4
	local tmp_results_file=$5
	local exp_name=$6
	local nf_args="${7:-}"

	local lcores=$(python3 -c "print(','.join('$DUT_CORES'.split(',')[:$n_cores]))")

	echo "[$exp_name] Running NF with $n_cores cores ($lcores)"

	if [[ ! -z "$nf_args" ]]; then
		run_nf "$nf_exe" "$lcores" "$nf_args"
	else 
		run_nf "$nf_exe" "$lcores"
	fi

	wait_for_nf "$nf_exe"

	for ((i=1;i<=$ITERATIONS;i++)); do
		echo "[$exp_name]   * Running latency benchmark {$i/$ITERATIONS, pcap=$pcap}"
		log "NF: $nf_exe, cores: $lcores, pcap: $pcap, it: $i/$ITERATIONS"

		replay_pcap_latency "$pcap" "$intermediate_results_file"
		mv $intermediate_results_file $tmp_results_file
	done

	echo "[$exp_name]   * Killing NF"
	kill_nf "$nf_exe"
}

run_bench_latency(){
	local nf_exe=$1
	local pcap=$2
	local exp_dir=$3
	local exp_name=$4
	local nf_args="${5:-}"

	local intermediate_results_file="$exp_dir/.single.csv"
	local tmp_results_file="$exp_dir/.results.csv"
	local results_file="$exp_dir/$exp_name.csv"

	__setup_bench "$nf_exe" "$tmp_results_file"

	local MIN_CORES=1
	if [[ ! -z "$nf_args" ]]; then
		__run_bench_with_n_cores_latency "$nf_exe" "$pcap" "$MIN_CORES" "$intermediate_results_file" "$tmp_results_file" "$exp_name" "$nf_args"
	else
		__run_bench_with_n_cores_latency "$nf_exe" "$pcap" "$MIN_CORES" "$intermediate_results_file" "$tmp_results_file" "$exp_name"
	fi

	__finalize_bench "$tmp_results_file" "$results_file"
}


run_bench() {
	local nf_exe=$1
	local pcap=$2
	local exp_dir=$3
	local exp_name=$4
	local nf_args="${5:-}"

	local intermediate_results_file="$exp_dir/.single.csv"
	local tmp_results_file="$exp_dir/.results.csv"
	local results_file="$exp_dir/$exp_name.csv"

	__setup_bench "$nf_exe" "$tmp_results_file"

	local MIN_CORES=1

	if [[ ! -z "$nf_args" ]]; then
		__run_bench_with_n_cores "$nf_exe" "$pcap" "$MIN_CORES" "$intermediate_results_file" "$tmp_results_file" "$exp_name" "$nf_args"
	else 
		__run_bench_with_n_cores "$nf_exe" "$pcap" "$MIN_CORES" "$intermediate_results_file" "$tmp_results_file" "$exp_name"
	fi

	__finalize_bench "$tmp_results_file" "$results_file"
}


bench_combination_nfs() {
	local nf_1=$1
	local nf_2=$2
	local config=$3
	local pcap=$4
	local exp_dir=$5
	local exp_name=$6

	tg_check_file "$TG_PCAPS_DIR/$pcap"
	dut_check_file "$DUT_COMBS_CONFIG_DIR/$config"
	set_log "$exp_dir"
	
	local nf_exe=$(build_nf "$nf_1" "$nf_2" "$config" "$exp_name")

	run_bench "$nf_exe" "$pcap" "$exp_dir" "$exp_name"
}

bench_combination_nfs_latency() {
	local nf_1=$1
	local nf_2=$2
	local config=$3
	local pcap=$4
	local exp_dir=$5
	local exp_name=$6

	tg_check_file "$TG_PCAPS_DIR/$pcap"
	dut_check_file "$DUT_COMBS_CONFIG_DIR/$config"
	set_log "$exp_dir"
	
	local nf_exe=$(build_nf "$nf_1" "$nf_2" "$config" "$exp_name")

	run_bench_latency "$nf_exe" "$pcap" "$exp_dir" "$exp_name"
}

build_nf_handmade() {

	local nf_1=$1
	local args=$2
	local exp_name=$3

	local nf_path="$DUT_COMBS_HM_DIR/$nf_1"

	#TODO cannot merge because build not working
	# if ! dut_run "stat nf.c > /dev/null 2>&1" "$merged_nf_path"; then 
	# 	#merge-nfs "$nf_path_1" "$nf_path_2" "$DUT_COMBS_CONFIG_DIR/$config" "$merged_nf_path"
	# fi

	if ! dut_run "stat $nf_path/build/app/nf > /dev/null 2>&1"; then 
		dut_run "cd $nf_path && make > /dev/null 2>&1"
	fi

	echo "$nf_path/build/app/nf"
}

bench_handmade_nf(){
	local nf=$1
	local pcap=$2
	local exp_dir=$3
	local exp_name=$4
	local nf_args=$5

	tg_check_file "$TG_PCAPS_DIR/$pcap"
	set_log "$exp_dir"

	local nf_exe=$(build_nf_handmade "$nf" "$nf_args" "$exp_name")

	run_bench "$nf_exe" "$pcap" "$exp_dir" "$exp_name" "$nf_args"
}

bench_handmade_nf_latency(){
	local nf=$1
	local pcap=$2
	local exp_dir=$3
	local exp_name=$4
	local nf_args=$5

	tg_check_file "$TG_PCAPS_DIR/$pcap"
	set_log "$exp_dir"

	local nf_exe=$(build_nf_handmade "$nf" "$nf_args" "$exp_name")

	run_bench_latency "$nf_exe" "$pcap" "$exp_dir" "$exp_name" "$nf_args"
}