#!/bin/bash

model="resnet50"
dataset="imagenet"

python run_optimizer.py \
	-vvv \
	--schedule ./examples/schedule/eyeriss_alex_conv2.json \
	--type basic \
	--arch ./examples/arch/3_level_mem_baseline_asic.json \
	--model $model \
	--dataset $dataset \
	2>&1 | tee logs/${model}_${dataset}.log
	#--network ./examples/layer/alex_conv2_batch16.json \

grep -v "Level\s*[0-9]" logs/${model}_${dataset}.log | grep -v "^$" > logs/${model}_${dataset}_out.log

