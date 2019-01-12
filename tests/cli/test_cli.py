import os

from collections import namedtuple
from unittest import TestCase
from unittest.mock import patch, Mock
from plan_b.cli import do_work


MockIssue = namedtuple('MockIssue', ['key', 'fields'])
MockFields = namedtuple('MockFields', [
    'issuetype', 'summary', 'assignee', 'reporter', 'created', 'resolutiondate', 'duedate', 'aggregatetimespent',
    'customfield_10073', 'priority', 'components', 'customfield_10180', 'customfield_16390', 'status', 'resolution',
    'customfield_13694', 'comments', 'aggregatetimeoriginalestimate', 'timeoriginalestimate'
])


def _make_mock_issue(
    key, issue_type, summary, assignee=None, reporter=None, created=None, resolved=None, due=None,
    time_spent=None, severity=None, priority=None, components=None, tags=None, qa_advice=None, status='open',
    resolution=None, epic_link=None, comments=None, aggregated_orig_estimate=None, orig_estimate=None
):
    return MockIssue(
        key=key,
        fields=MockFields(
            issuetype=namedtuple('issuetype', ['name'])(name=issue_type),
            summary=summary,
            assignee=namedtuple('assignee', ['name'])(name=assignee),
            reporter=reporter,
            created=created,
            resolutiondate=resolved,
            duedate=due,
            aggregatetimespent=time_spent,
            customfield_10073=namedtuple('customfield_10073', ['value'])(value=severity),
            priority=priority,
            components=components,
            customfield_10180=tags,
            customfield_16390=qa_advice,
            status=namedtuple('issuestatus', ['name'])(name=status),
            resolution=resolution,
            customfield_13694=epic_link,
            comments=comments,
            aggregatetimeoriginalestimate=aggregated_orig_estimate,
            timeoriginalestimate=orig_estimate
        )
    )


def _make_comment(author, body):
    return namedtuple(
        'comment', ['author', 'body']
    )(author=namedtuple('author', ['name'])(author), body=body)


def comments_side_effect(issue):
    # A1 project
    if issue.key == 'A-00001':
        return [
            _make_comment('V.Ivanov', '#plan reqs: hi, design: med, impl: 10d, doc: 1d, arch: 1d'),
            _make_comment('B.Smithson', '#plan qa: 1d'),
        ]
    elif issue.key == 'A-00002':
        return [
            _make_comment('J.Smith', '#plan reqs: hi, design: lo, impl: 5d, perf: 1w'),
            _make_comment('B.Smithson', '#plan qa: 2d'),
        ]
    elif issue.key == 'A-00003':
        return [
            _make_comment('V.Ivanov', '#plan reqs: lo, design: med, impl: 1d, doc: 1d'),
            _make_comment('J.Smith', '#plan reqs: med, design: lo, impl: 1w, doc: 1d'),
            _make_comment('B.Smithson', '#plan qa: 5d'),
            _make_comment('A.Testerson', '#plan qa: 1d'),
        ]
    elif issue.key == 'A-00005':
        return [
            _make_comment('V.Ivanov', '#plan reqs: lo, design: med, impl: 1d, doc: 1d'),
        ]
    # B2U4 project
    elif issue.key == 'A-00050':
        return [
            _make_comment('J.Smith', '#plan reqs: lo, design: lo, impl: 5w, doc: 1d, arch: 3d'),
            _make_comment('A.Testerson', '#plan qa: 3d'),
            _make_comment('B.Smithson', '#plan qa: 1d'),
        ]
    elif issue.key == 'A-00051':
        return [
            _make_comment('V.Ivanov', '#plan reqs: hi, design: lo, impl: 10w, doc: 1d, arch: 4d'),
            _make_comment('A.Testerson', '#plan qa: 2d'),
            _make_comment('B.Smithson', '#plan qa: 2d'),
        ]
    # qa specific epics
    elif issue.key == 'A-00006':
        return [
            _make_comment('B.Smithson', '#plan qa: 1w'),
            _make_comment('A.Testerson', '#plan qa: 2w')
        ]
    elif issue.key == 'A-00007':
        return [
            _make_comment('B.Smithson', '#plan qa: 3w'),
            _make_comment('A.Testerson', '#plan qa: 4w')
        ]
    elif issue.key == 'A-00008':
        return [
            _make_comment('B.Smithson', '#plan qa: 3w'),
        ]
    elif issue.key == 'A-00009':
        return [
            _make_comment('A.Testerson', '#plan qa: 1w')
        ]
    elif issue.key == 'A-00010':
        return [
            _make_comment('B.Smithson', '#plan qa: 1w'),
        ]
    return []


def issues_side_effect(data_query, **_):
    if 'A1' in data_query:
        return [
            _make_mock_issue('A-00001', 'Epic', 'Cool backend feature', assignee='V.Ivanov'),
            _make_mock_issue('A-00002', 'Epic', 'Super-duper UI improvement', assignee='J.Smith'),
            _make_mock_issue('A-00003', 'Epic', 'Revolutionary product', assignee='V.Ivanov'),
            _make_mock_issue(
                'A-00004', 'Story', 'Story inside A-00001', epic_link='A-00001', assignee='V.Ivanov'
            ),
            _make_mock_issue(
                'A-00005', 'Story', 'Autonomous story in another team\'s epic', epic_link='A-00100',
                assignee='V.Ivanov'
            ),
            _make_mock_issue('A-00006', 'Epic', 'A1 External QA Tasks', assignee='B.Smithson'),
            _make_mock_issue('A-00007', 'Epic', 'A1 Internal QA Tasks', assignee='B.Smithson'),
            _make_mock_issue('A-00008', 'Epic', 'A1 Regress', assignee='B.Smithson'),
            _make_mock_issue('A-00009', 'Epic', 'A1 Verification', assignee='B.Smithson'),
            _make_mock_issue('A-00010', 'Epic', 'A1 Production acceptance', assignee='B.Smithson'),
            _make_mock_issue('A-00021', 'Bug', '', assignee='V.Ivanov'),
            _make_mock_issue('A-00022', 'Bug', '', assignee='J.Smith'),
            _make_mock_issue('A-00023', 'Bug', '', assignee='J.Smith'),
            _make_mock_issue('A-00024', 'Bug', '', assignee='J.Smith'),
        ]
    elif 'B2U4' in data_query:
        return [
            _make_mock_issue('A-00050', 'Epic', 'Make go services great again', assignee='V.Ivanov'),
            _make_mock_issue('A-00051', 'Epic', 'Earn 10 billion $$$ for the company', assignee='V.Ivanov'),
            _make_mock_issue('A-00061', 'Bug', '', assignee='V.Ivanov', status='in progress'),
            _make_mock_issue('A-00062', 'Bug', '', assignee='V.Ivanov'),
            _make_mock_issue('A-00063', 'Bug', '', assignee='V.Ivanov'),
            _make_mock_issue('A-00064', 'Bug', '', assignee='J.Smith'),
        ]


class TestPlanExport(TestCase):

    @patch('jira.JIRA')
    def test_plan_export(self, jira_mock):
        jira_mock().search_issues = Mock(side_effect=issues_side_effect)
        jira_mock().comments = Mock(side_effect=comments_side_effect)

        data_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        do_work(
            os.path.join(data_dir_path, 'config-test.yml'),
            os.path.join(data_dir_path, 'test.xlsx')
        )
