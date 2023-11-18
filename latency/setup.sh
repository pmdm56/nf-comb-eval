CURRENT_EXPERIMENT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

FUNCTIONS_FILE="$CURRENT_EXPERIMENT_DIR/../evaluation.sh"
source $FUNCTIONS_FILE

nf1=fw_wan_1
nf2=nat_wan_1
nf3=pol_wan_1_lan_0
nf4=pol_wan_0_lan_1
config=config_bdd1.json
pcap=uniform_64B.pcap
pcap2=zipf-64B.pcap

nf_args_fw="--wan 1 --expire 100000000 --max-flows 65536 --eth-dest 0,01:23:45:67:89:00 --eth-dest 1,01:23:45:67:89:01 --lan 0 --rate 1000000000 --burst 10000000000 --capacity 65536"
nf_args_nat="--wan 1 --expire 100000000 --max-flows 65536 --eth-dest 0,01:23:45:67:89:00 --eth-dest 1,01:23:45:67:89:01 --lan 0 --rate 1000000000 --burst 10000000000 --capacity 65536 --extip 10.0.0.10 --starting-port 0"


# bench_combination_nfs_latency "$nf1" "$nf3" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf1}_${nf3}_${config%.json}_${pcap%.pcap}_latency"
# bench_combination_nfs_latency "$nf1" "$nf4" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf1}_${nf4}_${config%.json}_${pcap%.pcap}_latency"
# bench_combination_nfs_latency "$nf2" "$nf3" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf2}_${nf3}_${config%.json}_${pcap%.pcap}_latency"
# bench_combination_nfs_latency "$nf2" "$nf4" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf2}_${nf4}_${config%.json}_${pcap%.pcap}_latency"

# bench_handmade_nf_latency "fw_pol_down" "$pcap" $CURRENT_EXPERIMENT_DIR "hm_fw_pol_down_latency" "$nf_args_fw"
# bench_handmade_nf_latency "fw_pol_up" "$pcap" $CURRENT_EXPERIMENT_DIR "hm_fw_pol_up_latency" "$nf_args_fw"
# bench_handmade_nf_latency "nat_pol_down" "$pcap" $CURRENT_EXPERIMENT_DIR "hm_nat_pol_down_latency" "$nf_args_nat"
# bench_handmade_nf_latency "nat_pol_up" "$pcap" $CURRENT_EXPERIMENT_DIR "hm_nat_pol_up_latency" "$nf_args_nat"


bench_combination_nfs_latency "$nf1" "$nf3" "$config" "$pcap2" $CURRENT_EXPERIMENT_DIR "${nf1}_${nf3}_${config%.json}_${pcap2%.pcap}_latency"
bench_combination_nfs_latency "$nf1" "$nf4" "$config" "$pcap2" $CURRENT_EXPERIMENT_DIR "${nf1}_${nf4}_${config%.json}_${pcap2%.pcap}_latency"
bench_combination_nfs_latency "$nf2" "$nf3" "$config" "$pcap2" $CURRENT_EXPERIMENT_DIR "${nf2}_${nf3}_${config%.json}_${pcap2%.pcap}_latency"
bench_combination_nfs_latency "$nf2" "$nf4" "$config" "$pcap2" $CURRENT_EXPERIMENT_DIR "${nf2}_${nf4}_${config%.json}_${pcap2%.pcap}_latency"

bench_handmade_nf_latency "fw_pol_down" "$pcap2" $CURRENT_EXPERIMENT_DIR "hm_fw_pol_down_latency_zipf" "$nf_args_fw"
bench_handmade_nf_latency "fw_pol_up" "$pcap2" $CURRENT_EXPERIMENT_DIR "hm_fw_pol_up_latency_zipf" "$nf_args_fw"
bench_handmade_nf_latency "nat_pol_down" "$pcap2" $CURRENT_EXPERIMENT_DIR "hm_nat_pol_down_latency_zipf" "$nf_args_nat"
bench_handmade_nf_latency "nat_pol_up" "$pcap2" $CURRENT_EXPERIMENT_DIR "hm_nat_pol_up_latency_zipf" "$nf_args_nat"
