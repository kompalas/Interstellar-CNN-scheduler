import argparse
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', required=True, help='Logging file from the executed run')
    args = parser.parse_args()

    # read logfile
    with open(args.logfile, 'r') as f:
        log = f.read()

    total_layers = int(re.search("Beginning exploration for layer \S+? \(\d+/(\d+)", log).group(1))
    energy_measurements = [float(energy) for energy in re.findall("best energy:\s*([\d.]+)", log)]
    assert len(energy_measurements) == total_layers

    total_energy = sum(energy_measurements)
    print(f"Total energy: {total_energy:.3}")

    # TODO: what else can we get from the logfile?


if __name__ == "__main__":
    main()

