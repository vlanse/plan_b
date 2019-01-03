import logging
from collections import namedtuple, defaultdict
from typing import List

import jira
from dateutil import parser
from yarl import URL

from plan_b.issue import parse_work_estimate_text, Issue, Team, WorkEstimate
from plan_b.plan import IssuesDataSource
from plan_b.team import match_team_by_worker_name

log = logging.getLogger(__name__)


JiraIssue = namedtuple(
    'JiraIssue',
    [
        'key',
        'url',
        'type',
        'summary',
        'assignee',
        'reporter',
        'created',
        'resolved',
        'due',
        'time_spent',
        'severity',
        'priority',
        'components',
        'tags',
        'qa_advice',
        'status',
        'resolution',
        'epic_link',
        'comments',
        'aggregated_orig_estimate',
        'orig_estimate',
        'raw_issue'
    ]
)


JiraComment = namedtuple('JiraComment', ['author', 'body'])


WORKDAY_SECONDS = 28800  # 8 * 60 * 60


def make_jira_issue_from_raw_data(raw_issue, comments=tuple()) -> JiraIssue:
    jira_server = getattr(raw_issue, '_options', {'server': 'https://jira.domain'})['server']

    return JiraIssue(
        key=raw_issue.key,
        url=f'{jira_server}/browse/{raw_issue.key}',
        type=raw_issue.fields.issuetype.name,
        summary=raw_issue.fields.summary,
        assignee=raw_issue.fields.assignee,
        reporter=raw_issue.fields.reporter,
        created=parser.parse(raw_issue.fields.created) if raw_issue.fields.created else None,
        resolved=parser.parse(raw_issue.fields.resolutiondate) if raw_issue.fields.resolutiondate else None,
        due=parser.parse(raw_issue.fields.duedate) if raw_issue.fields.duedate else None,
        time_spent=raw_issue.fields.aggregatetimespent,
        severity=raw_issue.fields.customfield_10073.value
            if hasattr(raw_issue.fields, 'customfield_10073') and raw_issue.fields.customfield_10073 is not None
            else None,
        priority=raw_issue.fields.priority,
        components=str(raw_issue.fields.components),
        tags=str(raw_issue.fields.customfield_10180),
        qa_advice=raw_issue.fields.customfield_16390
            if hasattr(raw_issue.fields, 'customfield_16390') and raw_issue.fields.customfield_16390 is not None
            else None,
        status=raw_issue.fields.status.name,
        resolution=raw_issue.fields.resolution,
        epic_link=raw_issue.fields.customfield_13694 if raw_issue.fields.customfield_13694 else None,
        comments=comments,
        aggregated_orig_estimate=raw_issue.fields.aggregatetimeoriginalestimate,
        orig_estimate=raw_issue.fields.timeoriginalestimate,
        raw_issue=raw_issue
    )


class JiraIssuesDataSource(IssuesDataSource):

    def __init__(self, name: str, url: URL):
        super().__init__(name, url)
        self.jira_client = None

    @staticmethod
    def _find_and_parse_plan_comment(jira_issue: JiraIssue, team_by_name: dict) -> defaultdict:
        estimates_by_team = defaultdict(WorkEstimate)
        for comment in jira_issue.comments:
            estimate, team_name = parse_work_estimate_text(comment.body, comment.author, team_by_name)
            if estimate is None:
                continue
            if team_name is None:
                log.warning('Could not match team for %s', jira_issue.key)
            estimates_by_team[team_name] = estimate

        return estimates_by_team

    def export_issues(self, data_query: str, teams: List[Team]) -> List[Issue]:
        if not self.jira_client:
            self.jira_client = jira.JIRA(
                {
                    'server': str(URL.build(scheme=self.url.scheme, host=self.url.host))
                },
                basic_auth=(self.url.user, self.url.password)
            )

        jira_issues = []
        epics = set()

        log.debug('Searching issues for release with query "%s"', data_query)
        raw_issues = self.jira_client.search_issues(data_query, maxResults=10000)
        for raw_issue in raw_issues:
            jira_issue = make_jira_issue_from_raw_data(raw_issue)
            if jira_issue.type == 'Epic':
                epics.add(jira_issue.key)
            jira_issues.append(jira_issue)

        result = []
        for issue in jira_issues:
            if issue.type == 'Story' and issue.epic_link in epics:
                continue  # skip stories that are already in epics assigned to teams from plan

            log.debug('loading comments for issue %s', issue.key)
            comments = self.jira_client.comments(issue.raw_issue)
            issue = issue._replace(comments=tuple(JiraComment(x.author.name, x.body) for x in comments))

            result.append(issue)

        issues = []

        teams_by_name = {x.name: x for x in teams}
        for issue in result:
            log.debug('Scanning for #plan comment in issue %s', issue.key)
            estimates = self._find_and_parse_plan_comment(issue, teams_by_name)

            owner_team = match_team_by_worker_name(issue.assignee.name, teams)
            if owner_team is None:
                log.warning('Owner team is not a team from plan for %s', issue.key)
            issues.append(
                Issue(
                    issue.key,
                    issue.summary,
                    issue.url,
                    issue.status,
                    work_estimates=estimates,
                    owned_by_team=owner_team
                )
            )

        return issues
