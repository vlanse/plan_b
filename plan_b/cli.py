import locale
import logging

from argparse import ArgumentParser

from plan_b.exporters.config import make_capacity_plan_from_config

log = logging.getLogger(__name__)


def do_work(path_to_config: str, path_to_destination: str):
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")

    plan = make_capacity_plan_from_config(path_to_config)
    plan.export(path_to_destination)


def main():
    parser = ArgumentParser()
    parser.add_argument('--config', dest='config', help='path to config file')
    parser.add_argument('--destination', dest='destination', help='path to output file')
    args = parser.parse_args()

    do_work(args.config, args.destination)


if __name__ == '__main__':
    main()
