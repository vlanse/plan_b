import logging
from datetime import date
from typing import List
from yarl import URL

from plan_b.issue import Issue
from plan_b.team import Team

log = logging.getLogger(__name__)


class ProductRelease:

    def __init__(self, name: str, data_query: str = '', issues: List[Issue] = None):
        self.name = name
        self.data_query = data_query
        self.issues = issues if issues else []


class IssuesDataSource:

    def __init__(self, name: str = None, url: URL = None):
        self.name = name
        self.url = url

    def export_issues(self, data_query: str, teams: List[Team]) -> List[Issue]:
        raise NotImplementedError


class CapacityPlan:

    def __init__(
        self,
        start_date: date,
        end_date: date,
        production_calendar,
        issues_data_source: IssuesDataSource,
        teams: List[Team],
        releases: List[ProductRelease]
    ):
        self._teams = teams
        self._releases = releases
        self._start_date = start_date
        self._end_date = end_date
        self._issues_data_source = issues_data_source
        self._production_calendar = production_calendar

    def _export_issues_for_releases(self):
        for release in self._releases:
            log.info('Exporting work items for release %s', release.name)
            release.issues = self._issues_data_source.export_issues(release.data_query, self._teams)

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def production_calendar(self):
        return self._production_calendar

    @property
    def end_date(self) -> date:
        return self._end_date

    @property
    def releases(self) -> List[ProductRelease]:
        return self._releases

    @property
    def teams(self) -> List[Team]:
        return self._teams

    @property
    def data_source(self) -> IssuesDataSource:
        return self._issues_data_source
