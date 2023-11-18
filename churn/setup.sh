CURRENT_EXPERIMENT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

FUNCTIONS_FILE="$CURRENT_EXPERIMENT_DIR/../evaluation.sh"
source $FUNCTIONS_FILE

nf1=fw_wan_1
nf2=nat_wan_1
nf3=pol_wan_1_lan_0
nf4=pol_wan_0_lan_1
config=config_bdd1.json
EXPIRATION_TIME_US=1000

declare -a pcaps=(
    churn_15400fpm_64B_100Gbps_1000us.pcap
    churn_23000fpm_64B_100Gbps_1000us.pcap
    churn_31000fpm_64B_100Gbps_1000us.pcap
    churn_250000fpm_64B_100Gbps_1000us.pcap
    churn_885000fpm_64B_100Gbps_1000us.pcap
    churn_1500000fpm_64B_100Gbps_1000us.pcap
    churn_2000000fpm_64B_100Gbps_1000us.pcap
    churn_2600000fpm_64B_100Gbps_1000us.pcap
    churn_25000000fpm_64B_100Gbps_1000us.pcap
    churn_88462000fpm_64B_100Gbps_1000us.pcap
)

for pcap in "${pcaps[@]}"; do
    churn=$(echo "$pcap" | grep -oP "\\d+" | head -1)
    #bench_nf "$NF-$target-exp-time-$EXPIRATION_TIME_US-us" "$NF" "$target" "$pcap" "$CURRENT_EXPERIMENT_DIR" "churn-$target-$churn-fpm"
    bench_combination_nfs "$nf1" "$nf3" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf1}_${nf3}_${config%.json}_${churn}-fpm"
    bench_combination_nfs "$nf1" "$nf4" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf1}_${nf4}_${config%.json}_${churn}-fpm"
    bench_combination_nfs "$nf2" "$nf3" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf2}_${nf3}_${config%.json}_${churn}-fpm"  
    bench_combination_nfs "$nf2" "$nf4" "$config" "$pcap" $CURRENT_EXPERIMENT_DIR "${nf2}_${nf4}_${config%.json}_${churn}-fpm"
done
