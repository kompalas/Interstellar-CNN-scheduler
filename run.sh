#!/bin/bash

model="${1:-resnet50}"
dataset="imagenet"

python run_optimizer.py \
	-vv \
	--type basic \
	--arch ./examples/arch/bal_mem_arch.json \
	--model $model \
	--dataset $dataset \
	2>&1 | tee logs/${model}_${dataset}.log
	#--network ./examples/layer/alex_conv2_batch16.json \
	#--schedule ./examples/schedule/eyeriss_alex_conv2.json \

grep -v "Level\s*[0-9]" logs/${model}_${dataset}.log | grep -v "^$"  | grep -v "Find best order for schedule" > logs/${model}_${dataset}_out.log

