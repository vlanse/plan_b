from unittest import TestCase

from plan_b.issue import parse_work_estimate_text, ConfidenceLevel
from plan_b.team import Team, Worker


teams = {
    'a': Team('a', [Worker('V.Ivanov'), Worker('P.Smirnov')]),
    'b': Team('b', [Worker('A.Petrov'), Worker('S.Kuznetsov')])
}


class TestEstimateParsing(TestCase):

    def test_whitespaces_before_after(self):
        text_with_tabs_spaces_and_linebreaks =\
"""

        #plan

"""
        self.assertIsNotNone(parse_work_estimate_text(text_with_tabs_spaces_and_linebreaks, '', {})[0])

    def test_invalid_start_tag(self):
        text_with_invalid_tag = ' # plan '
        self.assertIsNone(parse_work_estimate_text(text_with_invalid_tag, '', {})[0])

    def test_basic_parsing(self):
        text = \
"""
#plan
reqs confidence: high,
 design : med; arch: 4h;
 , perf : 2d;
 impl:   1w, 
 doc:  0.5w;;
"""
        r, possible_team = parse_work_estimate_text(text, 'Vasily.Ivanov', teams)
        self.assertEqual(ConfidenceLevel.High, r.reqs_level)
        self.assertEqual(ConfidenceLevel.Medium, r.design_level)
        self.assertEqual(4 * 60 * 60, r.arch_design)
        self.assertEqual(2 * 8 * 60 * 60, r.perf_design)
        self.assertEqual(1 * 5 * 8 * 60 * 60, r.implementation)
        self.assertEqual(int(0.5 * 5 * 8 * 60 * 60), r.documentation)
        self.assertEqual('a', possible_team)

    def test_explicit_team_specification(self):
        text = \
"""
#plan
reqs confidence: high,
 design : med; arch: 4h
team: b
"""
        _, possible_team = parse_work_estimate_text(text, 'Mr.Coordinator', teams)
        self.assertEqual('b', possible_team)

    def test_real_comment(self):
        text = \
"""
#plan
reqs: hi, design: med, impl: 10d
design med because IPN client lib itself is not finalized yet
+ 3d - need to get data about licenses from License server
"""
        r, possible_team = parse_work_estimate_text(text, 'Vasily.Ivanov', teams)
        self.assertEqual(ConfidenceLevel.High, r.reqs_level)
        self.assertEqual(ConfidenceLevel.Medium, r.design_level)
        self.assertEqual(10 * 8 * 60 * 60, r.implementation)
        self.assertEqual('a', possible_team)
