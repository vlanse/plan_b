import logging
from datetime import date
from typing import List, Tuple, Dict
from yarl import URL

from plan_b.issue import Issue
from plan_b.team import Team

log = logging.getLogger(__name__)


class Project:

    def __init__(self, name: str, data_query: str = ''):
        self.name: str = name
        self.data_query: str = data_query
        self.issues: List[Issue] = []
        self.known_bugs_count: Dict[Team, int] = 0


class IssuesDataSource:

    def __init__(self, name: str = None, url: URL = None):
        self.name: str = name
        self.url: URL = url

    def export_issues(self, data_query: str, teams: List[Team]) -> Tuple[List[Issue], Dict[Team, int]]:
        raise NotImplementedError


class CapacityPlan:

    def __init__(
        self,
        start_date: date,
        end_date: date,
        production_calendar,
        issues_data_source: IssuesDataSource,
        teams: List[Team],
        projects: List[Project]
    ):
        self._teams: List[Team] = teams
        self._projects: List[Project] = projects
        self._start_date: date = start_date
        self._end_date: date = end_date
        self._issues_data_source: IssuesDataSource = issues_data_source
        self._production_calendar = production_calendar

    def _export_issues_for_projects(self):
        for project in self._projects:
            log.info('Exporting work items for project %s', project.name)
            issues, known_bugs_count = self._issues_data_source.export_issues(project.data_query, self._teams)
            project.issues = issues
            project.known_bugs_count = known_bugs_count

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
    def projects(self) -> List[Project]:
        return self._projects

    @property
    def teams(self) -> List[Team]:
        return self._teams

    @property
    def data_source(self) -> IssuesDataSource:
        return self._issues_data_source
