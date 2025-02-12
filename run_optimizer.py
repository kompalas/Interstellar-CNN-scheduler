import os
import numpy as np
import argparse
import math
import time
import re
import cnn_mapping as cm
from glob import glob


def basic_optimizer(arch_info, network_info, schedule_info=None, basic=False, verbose=False):    

    resource = cm.Resource.arch(arch_info) 
    layer = cm.Layer.layer(network_info)
    schedule = cm.Schedule.schedule(schedule_info) if schedule_info != None else None
    opt_result = cm.optimizer.opt_optimizer(resource, layer, schedule, verbose)
    
    level_costs = cm.cost_model.get_level_costs(resource, opt_result[1], layer, verbose)
    if verbose or basic:
        print("best energy: ", opt_result[0])
        print("cost for each level: ", level_costs) #TODO
        print("best schedule: ", cm.utils.print_loop_nest(opt_result[1]))
    return opt_result[0]


def mem_explore_optimizer(arch_info, network_info, schedule_info, verbose=False):
   
    assert "explore_points" in arch_info, "missing explore_points in arch file" 
    assert "capacity_scale" in arch_info, "missing capacity_scale in arch file" 
    assert "access_cost_scale" in arch_info, "missing access_cost_scale in arch file" 
    cwd = os.getcwd()
#    output_filename = os.path.join(cwd, "dataset", network_info['layer_name'] + '_128.csv')
    explore_points = arch_info["explore_points"]
    energy_list = np.zeros(tuple(explore_points))
    summary_array = np.zeros([np.product(explore_points), 12])
    #TODO support more than two levels of explorations
    capacity0 = arch_info["capacity"][0]
    capacity1 = arch_info["capacity"][1]
    cost0 = arch_info["access_cost"][0]
    cost1 = arch_info["access_cost"][1]
    i = 0
    for x in range(explore_points[0]):
        arch_info["capacity"][0] = capacity0 * (arch_info["capacity_scale"][0]**x)
        arch_info["access_cost"][0] = cost0 * (arch_info["access_cost_scale"][0]**x)
        for y in range(explore_points[1]):
            #if x == 0 and y < 1:
            #    continue
            arch_info["capacity"][1] = capacity1 * (arch_info["capacity_scale"][1]**y)
            arch_info["access_cost"][1] = cost1 * (arch_info["access_cost_scale"][1]**y)
            print(arch_info)
            energy = basic_optimizer(arch_info, network_info, schedule_info, False, verbose)
            energy_list[x][y] = energy
            cur_point = network_info["layer_info"] + arch_info["capacity"][:-1] + [energy]
            summary_array[i] = cur_point
#            np.savetxt(output_filename, summary_array, delimiter=",")
            i += 1

    print(list(energy_list))
    print("optiaml energy for all memory systems: ", np.min(np.array(energy_list)))

def mac_explore_optimizer(arch_info, network_info, schedule_info, verbose=False):
    
    dataflow_res = []
    #TODO check the case when parallel count larger than layer dimension size
    dataflow_generator = dataflow_generator_function(arch_info)

    for dataflow in dataflow_generator:
        energy = basic_optimizer(arch_info, network_info, schedule_info, False, verbose)            
        dataflow_res.append[energy]
        
    if verbose:
        print("optimal energy for all dataflows: ", dataflow_res)

    return dataflow_res


def dataflow_explore_optimizer(arch_info, network_info, file_name, verbose=False):

    assert arch_info["parallel_count"] > 1, \
        "parallel count has to be more than 1 for dataflow exploration"

    resource = cm.Resource.arch(arch_info) 
    layer = cm.Layer.layer(network_info)
    dataflow_tb = cm.mapping_point_generator.dataflow_exploration(resource, layer, file_name, verbose)
    
    if verbose:
        print("dataflow table done ")


if __name__ == "__main__":

    # root directory of this project
    maindir = os.path.dirname(__file__)
    layerdir = os.path.join(maindir, 'examples', 'model_layers')
    layer_files = glob(f"{layerdir}/*.json")
    assert len(layer_files) > 0, f"No files that describe DNN layers were found under {layerdir}"

    # define options for DNN models
    ALL_MODELS = list(set([re.search(".*/(.*?)_", layer_file).group(1) for layer_file in layer_files]))

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", required=True, choices=["basic", "mem_explore", "dataflow_explore"],
                        default="basic", help="optimizer type")
    parser.add_argument("-a", "--arch", required=True, help="architecture specification")
    #parser.add_argument("network", help="network specification")
    parser.add_argument("-m", "--model", required=True, choices=ALL_MODELS, default="resnet50",
                        help="model name")
    parser.add_argument("-d", "--dataset", required=True, choices=['cifar10', 'cifar100', 'imagenet'],
                        default='imagenet', help='dataset name')
    parser.add_argument("-s", "--schedule", help="restriction of the schedule space")
    parser.add_argument("-n", "--name", default="dataflow_table", help="name for the dumped pickle file")
    parser.add_argument("-v", "--verbose", action='count', help="vebosity")
    args = parser.parse_args()

    # keep only relevant layer files and sort based on layer index
    layer_files = sorted([layer_file for layer_file in layer_files if args.model + '_' + args.dataset in layer_file],
                         key=lambda fn: int(re.search("_layer(\d+?)_", fn).group(1)), reverse=False)

    for layer_file in layer_files:
        _, _, layer_idx, layer_name = re.search(".*/(.*?).json", layer_file).group(1).split("_")
        layer_idx = int(layer_idx.replace("layer", ""))
        print("Beginning exploration for layer {} ({}/{})".format(
              layer_name, layer_idx + 1, len(layer_files)))

        start = time.time()
        # get information about the current layer
        args.network = layer_file
        arch_info, network_info, schedule_info = cm.extract_input.extract_info(args)    
        if args.type == "basic":
            basic_optimizer(arch_info, network_info, schedule_info, True, args.verbose)
        elif args.type == "mem_explore":
            mem_explore_optimizer(arch_info, network_info, schedule_info, args.verbose)
        elif args.type == "dataflow_explore":
            dataflow_explore_optimizer(arch_info, network_info, args.name, args.verbose)
        print("Completed exploration for layer {} ({}/{}) in {:.3e}s".format(
              layer_name, layer_idx + 1, len(layer_files), time.time() - start))

