import re
from enum import Enum
from typing import Optional, List, Tuple, Dict
from collections import defaultdict

from plan_b.team import Team, match_team_by_worker_name


class ConfidenceLevel(Enum):
    High = 1
    Medium = 1.5
    Low = 2


class WorkEstimate:

    def __init__(
        self,
        reqs_level: ConfidenceLevel = None,
        design_level: ConfidenceLevel = None,
        arch_design: int = None,
        perf_design: int = None,
        implementation: int = None,
        documentation: int = None,
        qa_effort: int = None
    ):
        self.reqs_level: ConfidenceLevel = reqs_level
        self.design_level: ConfidenceLevel = design_level
        self.arch_design: int = arch_design
        self.perf_design: int = perf_design
        self.implementation: int = implementation
        self.documentation: int = documentation
        self.qa_effort: int = qa_effort


class Issue:

    def __init__(
        self,
        issue_key: str,
        issue_summary: str = None,
        # TODO use yarl.URL
        issue_url: str = None,
        issue_status: str = None,
        owned_by_team: Team = None,
        work_estimates: defaultdict = None
    ):
        self.issue_key: str = issue_key
        self.issue_summary: str = issue_summary
        self.issue_url: str = issue_url
        self.issue_status: str = issue_status
        self.owned_by_team: Team = owned_by_team

        self.orig_estimates_by_team: Dict[str, WorkEstimate] = work_estimates or defaultdict(WorkEstimate)
        self.remaining_estimates_by_team: Dict[str, WorkEstimate] = defaultdict(WorkEstimate)

        if self.issue_status is not None and self.issue_status.lower() in ('closed', 'resolved', 'done'):
            for team_name, estimates in self.orig_estimates_by_team.items():
                self.remaining_estimates_by_team[team_name] = WorkEstimate(
                    reqs_level=estimates.reqs_level,
                    design_level=estimates.design_level,
                    arch_design=0,
                    perf_design=0,
                    implementation=0,
                    documentation=0,
                    qa_effort=0
                )
        else:
            self.remaining_estimates_by_team = self.orig_estimates_by_team


SEPARATORS_RX = re.compile('[;\n]')


def seconds_to_man_weeks(seconds: int) -> float:
    return seconds / (60 * 60 * 8 * 5)


def _parse_confidence_level(level: str) -> ConfidenceLevel:
    if level in ['hi', 'high']:
        return ConfidenceLevel.High
    elif level in ['med', 'medium']:
        return ConfidenceLevel.Medium
    elif level in ['low', 'lo']:
        return ConfidenceLevel.Low
    else:
        raise ValueError(f'invalid confidence level value: {level}')


def _parse_estimation(value: str) -> int:
    unit_spec = value[-1]
    if unit_spec not in ['h', 'd', 'w']:
        raise ValueError(f'Incorrect estimation specification {value}, it must end with a unit spec, e.g. h, d or w')
    value = float(value[0:-1].strip())
    if unit_spec == 'h':
        return int(value * 60 * 60)
    elif unit_spec == 'd':
        return int(value * 8 * 60 * 60)
    elif unit_spec == 'w':
        return int(value * 5 * 8 * 60 * 60)


def _set_property(
    estimate: WorkEstimate,
    property_name: str,
    possible_names: List[str],
    data_name: str,
    data_value: str,
    value_parser
) -> bool:
    if data_name in possible_names:
        if getattr(estimate, property_name) is not None:
            raise RuntimeError(f'{property_name} already specified in comment')
        setattr(estimate, property_name, value_parser(data_value))
        return True
    return False


POSSIBLE_REQS_LEVEL_TOKENS = ['reqs', 'requirements', 'requirements confidence', 'reqs confidence', 'reqs level']
POSSIBLE_DESIGN_LEVEL_TOKENS = ['design', 'design confidence', 'design level']
POSSIBLE_ARCH_DESIGN_TOKENS = ['arch', 'architecture', 'arch design', 'architecture design']
POSSIBLE_PERF_DESIGN_TOKENS = ['perf', 'perf engineering', 'performance engineering', 'performance']
POSSIBLE_IMPL_TOKENS = ['impl', 'implementation', 'implementing']
POSSIBLE_DOCUMENTATION_TOKENS = ['doc', 'documentation', 'documenting']
POSSIBLE_TEAM_TOKENS = ['team']
POSSIBLE_QA_EFFORT_TOKENS = ['qa', 'qa effort', 'qa acceptance']

POSSIBLE_TOKENS = \
        POSSIBLE_REQS_LEVEL_TOKENS \
        + POSSIBLE_DESIGN_LEVEL_TOKENS \
        + POSSIBLE_ARCH_DESIGN_TOKENS \
        + POSSIBLE_PERF_DESIGN_TOKENS \
        + POSSIBLE_IMPL_TOKENS \
        + POSSIBLE_DOCUMENTATION_TOKENS \
        + POSSIBLE_TEAM_TOKENS \
        + POSSIBLE_QA_EFFORT_TOKENS


def parse_work_estimate_text(
    text: str,
    author_name: str,
    team_by_name: dict
) -> Tuple[Optional[WorkEstimate], Optional[str]]:
    text = text.strip()

    if not text.startswith('#plan'):
        return None, None

    text = text.replace('#plan', '').strip()

    text = re.sub(SEPARATORS_RX, ',', text)

    lines = [t for t in [x.strip() for x in text.split(',')] if t]
    # TODO do it smarter
    tokens = []
    for l in lines:
        for start in POSSIBLE_TOKENS:
            if l.startswith(start):
                tokens.append(l)
                break

    kv = {k.strip().lower(): v.strip().lower() for k, v in [x.split(':') for x in tokens if ':' in x]}

    matching_team_name = None
    result = WorkEstimate()
    for k, v in kv.items():
        (
            _set_property(result, 'reqs_level', POSSIBLE_REQS_LEVEL_TOKENS, k, v, _parse_confidence_level)
            or _set_property(result, 'design_level', POSSIBLE_DESIGN_LEVEL_TOKENS, k, v, _parse_confidence_level)
            or _set_property(result, 'arch_design', POSSIBLE_ARCH_DESIGN_TOKENS, k, v, _parse_estimation)
            or _set_property(result, 'perf_design', POSSIBLE_PERF_DESIGN_TOKENS, k, v, _parse_estimation)
            or _set_property(result, 'implementation', POSSIBLE_IMPL_TOKENS, k, v, _parse_estimation)
            or _set_property(result, 'documentation', POSSIBLE_DOCUMENTATION_TOKENS, k, v, _parse_estimation)
            or _set_property(result, 'qa_effort', POSSIBLE_QA_EFFORT_TOKENS, k, v, _parse_estimation)
        )

        # TODO: implement better matching
        if k in POSSIBLE_TEAM_TOKENS:
            for team_name in team_by_name.keys():
                if v in team_name.lower():
                    matching_team_name = team_name

    if matching_team_name is None:
        # if no explicit team specified, try to match by comment author
        team = match_team_by_worker_name(author_name, [x for x in team_by_name.values()])
        if team:
            matching_team_name = team.name

    return result, matching_team_name
