import logging
import os
import re
from calendar import month_abbr
from collections import defaultdict
from datetime import date
from typing import List

import yaml
from yarl import URL

from plan_b.team import Team, make_worker, Worker, make_team
from plan_b.plan import ProductRelease, CapacityPlan, IssuesDataSource
from plan_b.date_utils import get_months_range
from plan_b.exporters.xlsx import export_plan
from plan_b.exporters.xlsx.metadata import load_metadata
from plan_b.issue_data_sources.jira import JiraIssuesDataSource

SEPARATORS_RX = re.compile('[ \t;]')


log = logging.getLogger(__name__)


def read_teams_from_config(config: dict) -> List[Team]:
    teams = []
    for t in config.get('teams', []):
        workers: List[Worker] = []
        for m in t.get('members', []):
            workers.append(
                make_worker(name=m['name'], efficiency=m.get('efficiency'), works_since=m.get('works_since'))
            )
        teams.append(make_team(t['name'], workers))
    return teams


def read_releases_from_config(config: dict) -> List[ProductRelease]:
    releases = []
    for r in config.get('releases', []):
        r = ProductRelease(r['name'], r['data_query'])
        releases.append(r)
    return releases


def read_data_sources_from_config(config: dict) -> List[IssuesDataSource]:
    sources = []
    for ds in config.get('issue_data_sources', []):
        if ds['type'] != 'jira':
            raise RuntimeError(f'Unknown data source type {ds["type"]}')

        sources.append(JiraIssuesDataSource(ds['name'], URL(ds['url'])))
    return sources


def make_production_calendar(calendar_description: dict) -> defaultdict:
    """
    Dict of lists indexed by year, each list contains dicts for each month of the year,
    which has the following keys:
    holidays -> set of holidays (exceptions from regular weekends)
    workdays -> set of workdays (in addition to regular workdays, e.g. Mon-Fri)
    """
    result = defaultdict(list)
    for year, months in calendar_description.items():
        result_months = []
        for dt in get_months_range(start_date=date(year, 1, 1), end_date=date(year, 12, 1)):
            result_month = {'holidays': set(), 'workdays': set()}
            month_name = month_abbr[dt.month]
            month_config = re.sub(SEPARATORS_RX, ',', str(months.get(month_name, '')))
            items = month_config.split(',')

            for item in items:
                if '-' in item:
                    dates = item.split('-')
                    if len(dates) != 2:
                        raise RuntimeError(f'Invalid holiday dates interval \"{item}\" in {month_name}')
                    for day in range(int(dates[0]), int(dates[1]) + 1):
                        result_month['holidays'].add(day)

                if item.isdigit():
                    result_month['holidays'].add(int(item))

                if item.startswith('x'):
                    result_month['workdays'].add(int(item.replace('x', '')))

            result_months.append(result_month)
        result[year] = result_months
    return result


class XlsxCapacityPlan(CapacityPlan):

    def __init__(self, output_file_path: str, **kwargs):
        super().__init__(**kwargs)
        self._output_file = output_file_path

    def export(self):
        plan_edits = None
        if os.path.exists(self._output_file):
            log.info('Output file %s already exists, trying to load its content and scan for changes', self._output_file)
            plan_edits = load_metadata(self._output_file)
            log.info('Changes loaded, removing previous file and creating a new one inplace')
            os.unlink(self._output_file)

        self._export_issues_for_releases()

        log.info('Exporting plan to file %s', self._output_file)
        export_plan(
            self.releases,
            self.teams,
            self.start_date,
            self.end_date,
            self.production_calendar,
            self._output_file,
            plan_edits
        )


def make_capacity_plan_from_config(config_file_path: str) -> XlsxCapacityPlan:
    log.debug('Loading capacity plan from file %s', config_file_path)
    with open(config_file_path) as config_file:
        config = yaml.load(config_file)

    p = config['plan']

    teams = []
    for t in p['teams']:
        team = list(filter(lambda x: x.name == t, read_teams_from_config(config)))
        if len(team) != 1:
            raise RuntimeError(f'Invalid plan teams configuration for "{t}", found {len(team)} items')
        teams.append(team[0])

    releases = []
    for r in p['releases']:
        release = list(filter(lambda x: x.name == r, read_releases_from_config(config)))
        if len(release) != 1:
            raise RuntimeError(f'Invalid plan releases configuration for "{r}", found {len(release)} items')
        releases.append(release[0])

    ds_name = p['data_source']
    data_sources = list(filter(lambda x: x.name == ds_name, read_data_sources_from_config(config)))
    if len(data_sources) != 1:
        raise RuntimeError(f'Invalid plan data source configuration for "{ds_name}", found {len(data_sources)} items')

    return XlsxCapacityPlan(
        output_file_path=p['output_file'],
        start_date=p['period']['start_date'],
        end_date=p['period']['end_date'],
        production_calendar=make_production_calendar(config.get('production_calendar', dict())),
        issues_data_source=data_sources[0],
        teams=teams,
        releases=releases
    )
