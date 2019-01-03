from typing import Dict, List, Tuple
from enum import IntEnum

from plan_b.team import Team
from plan_b.plan import ProductRelease, Issue
from plan_b.issue import seconds_to_man_weeks
from plan_b.exporters.xlsx.utils import Pos, RelPos, write_row, Region
from plan_b.exporters.xlsx.metadata import CellReference
from plan_b.exporters.xlsx import formats
from plan_b.exporters.xlsx.utils import merge_cells, merge_dicts


class BorderPos(IntEnum):
    Left = 1
    Right = 2


def _get_format_for_confidence_level(level: int, border_pos: BorderPos):
    format_desc = {}
    if level == 1:
        format_desc = formats.CONF_LEVEL_HIGH.copy()
    elif 1 < level <= 1.5:
        format_desc = formats.CONF_LEVEL_MED.copy()
    elif 1.5 < level:
        format_desc = formats.CONF_LEVEL_LOW.copy()

    if border_pos == BorderPos.Right:
        format_desc.update(formats.NUMERIC_BORDER_RIGHT)
    elif border_pos == BorderPos.Left:
        format_desc.update(formats.NUMERIC_BORDER_LEFT)

    return formats.get_format(format_desc)


def _create_cells_for_issue(issue: Issue, teams: List[Team], offset: Pos) -> List:
    dev_teams = [team for team in teams if team.is_dev()]

    values = [
        [{'url': issue.issue_url, 'string': issue.issue_key}, 'write_url'],
        issue.issue_summary,
    ]

    # requirements confidence level
    reqs_level = 0 if issue.owned_by_team and issue.owned_by_team.is_qa() else \
        (max([item.reqs_level.value for item in issue.remaining_estimates_by_team.values() if item.reqs_level] or [2]))
    values.append([reqs_level, _get_format_for_confidence_level(reqs_level, BorderPos.Left)])
    reqs_level_pos = RelPos(offset, column=len(values) - 1)

    # design confidence level
    design_level = 0 if issue.owned_by_team and issue.owned_by_team.is_qa() else \
        (
            max(
                [
                    item.design_level.value
                    for item in issue.remaining_estimates_by_team.values() if item.design_level]
                or [2]
            )
        )
    values.append([design_level, _get_format_for_confidence_level(design_level, BorderPos.Right)])
    design_level_pos = RelPos(offset, column=len(values) - 1)

    arch_design = seconds_to_man_weeks(
        sum(item.arch_design or 0 for item in issue.remaining_estimates_by_team.values())
    )
    values.append([arch_design, formats.numeric_format])
    arch_design_pos = RelPos(offset, column=len(values) - 1)

    team_impl_pos = {}
    for i in range(len(dev_teams)):
        team = dev_teams[i]
        values.append([
            seconds_to_man_weeks(issue.remaining_estimates_by_team[team.name].implementation or 0),
            formats.numeric_border_left_format if i == 0 else formats.numeric_format
        ])
        team_impl_pos[team.name] = RelPos(offset, column=len(values) - 1)
    # total for impl and unit tests
    values.append([
        f'=SUM('
        f'{RelPos(offset, column=len(values) - len(dev_teams)).to_cell()}'
        f':{RelPos(offset, column=len(values) - 1).to_cell()}'
        f')',
        formats.numeric_border_right_format
    ])
    impl_total_pos = RelPos(offset, column=len(values) - 1)

    values.append(f'={impl_total_pos.to_cell()} * 0.1')  # integration
    integration_pos = RelPos(offset, column=len(values) - 1)

    values.append(f'={impl_total_pos.to_cell()} * 0.2')  # test automation
    test_automation_pos = RelPos(offset, column=len(values) - 1)

    values.append(f'={impl_total_pos.to_cell()} * 0.3')  # stabilization
    stabilization_pos = RelPos(offset, column=len(values) - 1)

    values.append(
        seconds_to_man_weeks(sum(item.documentation or 0 for item in issue.remaining_estimates_by_team.values()))
    )
    documentation_pos = RelPos(offset, column=len(values) - 1)

    for i in range(len(dev_teams)):
        team = dev_teams[i]
        values.append([
            seconds_to_man_weeks(issue.remaining_estimates_by_team[team.name].perf_design or 0),
            formats.numeric_border_left_format if i == 0 else formats.numeric_format
        ])
    # total for perf engineering
    values.append([
        f'=SUM('
        f'{RelPos(offset, column=len(values) - len(dev_teams)).to_cell()}'
        f':{RelPos(offset, column=len(values) - 1).to_cell()}'
        f')',
        formats.numeric_border_right_format
    ])
    perf_engineering_pos = RelPos(offset, column=len(values) - 1)

    totals_pos = RelPos(offset, column=len(values) + len(dev_teams))
    for i in range(len(dev_teams)):
        team = dev_teams[i]
        d = f'=IF({impl_total_pos.to_cell()}<>0,' \
            f'{totals_pos.to_cell()}*{team_impl_pos[team.name].to_cell()}/{impl_total_pos.to_cell()}' \
            f',0)'
        values.append([d, formats.numeric_border_left_format if i == 0 else formats.numeric_format])

    # feature dev total
    values.append([
        f'=('
        f'{arch_design_pos.to_cell()}'
        f'+{impl_total_pos.to_cell()}'
        f'+{integration_pos.to_cell()}'
        f'+{test_automation_pos.to_cell()}'
        f'+{stabilization_pos.to_cell()}'
        f'+{documentation_pos.to_cell()}'
        f'+{perf_engineering_pos.to_cell()}'
        f')'
        f'*{reqs_level_pos.to_cell()}'
        f'*{design_level_pos.to_cell()}',
        formats.numeric_border_right_format
    ])
    feature_dev_total_pos = RelPos(offset, column=len(values) - 1)

    # qa effort
    qa_teams = [team for team in teams if team.is_qa()]
    for i in range(len(qa_teams)):
        team = qa_teams[i]
        values.append([
            seconds_to_man_weeks(issue.remaining_estimates_by_team[team.name].qa_effort or 0),
            formats.numeric_border_left_format if i == 0 else formats.numeric_format
        ])
    # total for qa effort
    values.append([
        f'=SUM('
        f'{RelPos(offset, column=len(values) - len(qa_teams)).to_cell()}'
        f':{RelPos(offset, column=len(values) - 1).to_cell()}'
        f')',
        formats.numeric_border_right_format
    ])
    qa_effort_total_pos = RelPos(offset, column=len(values) - 1)

    # feature total
    values.append(
        f'='
        f'{feature_dev_total_pos.to_cell()}'
        f'+{qa_effort_total_pos.to_cell()}'
    )
    return values


def _create_release_table_header(sheet, teams: List[Team], offset=Pos()) -> Region:
    dev_teams = [team for team in teams if team.is_dev()]
    qa_teams = [team for team in teams if team.is_qa()]

    column_count = 14 + 3 * len(dev_teams) + len(qa_teams)

    merge_cells(sheet, RelPos(offset, 1, 0), RelPos(offset, 2, 0), 'Key', formats.centered_header_format)
    merge_cells(sheet, RelPos(offset, 1, 1), RelPos(offset, 2, 1), 'Summary', formats.centered_header_format)

    merge_cells(sheet, RelPos(offset, 1, 2), RelPos(offset, 1, 3), 'Confidence', formats.centered_header_border_format)

    _, col = merge_cells(
        sheet,
        RelPos(offset, 1, 4),
        RelPos(offset, 2, 4),
        'Arch design',
        formats.centered_vertical_text_header_format,
        width=5
    )

    merge_cells(
        sheet, RelPos(offset, 1, 5), RelPos(offset, 1, 5 + len(dev_teams)),
        'Impl & unit tests', formats.centered_header_border_format
    )

    rel_offset = RelPos(offset, 0, 5 + len(dev_teams) + 1)
    merge_cells(
        sheet,
        RelPos(rel_offset, 1, 0),
        RelPos(rel_offset, 2, 0),
        'Integration',
        formats.centered_vertical_text_header_format,
        width=5
    )
    merge_cells(
        sheet,
        RelPos(rel_offset, 1, 1),
        RelPos(rel_offset, 2, 1),
        'Test automation',
        formats.centered_vertical_text_header_format,
        width=5
    )
    merge_cells(
        sheet,
        RelPos(rel_offset, 1, 2),
        RelPos(rel_offset, 2, 2),
        'Stabilization',
        formats.centered_vertical_text_header_format,
        width=5
    )
    merge_cells(
        sheet,
        RelPos(rel_offset, 1, 3),
        RelPos(rel_offset, 2, 3),
        'Documentation',
        formats.centered_vertical_text_header_format,
        width=5
    )
    merge_cells(
        sheet, RelPos(rel_offset, 1, 4), RelPos(rel_offset, 1, 4 + len(dev_teams)),
        'Perf engineering', formats.centered_header_border_format
    )
    rel_offset = RelPos(rel_offset, 0, 4 + len(dev_teams) + 1)
    merge_cells(
        sheet, RelPos(rel_offset, 1, 0), RelPos(rel_offset, 1, len(dev_teams)),
        'Feature dev subtotal', formats.centered_header_border_format
    )
    rel_offset = RelPos(rel_offset, 0, len(dev_teams) + 1)

    merge_cells(
        sheet, RelPos(rel_offset, 1, 0), RelPos(rel_offset, 1, len(qa_teams)),
        'QA effort', formats.centered_header_border_format
    )
    rel_offset = RelPos(rel_offset, 1, len(qa_teams))

    merge_cells(
        sheet, RelPos(rel_offset, 0, 1), RelPos(rel_offset, 1, 1), 'Feature total', formats.centered_header_format
    )

    write_row(
        sheet,
        RelPos(offset, 2, 2),
        cell_generator=[
            ['Reqs', formats.centered_vertical_text_header_left_border_format],
            ['Design', formats.centered_vertical_text_header_right_border_format]
        ],
        col_width=5
    )

    rel_offset = RelPos(offset, 2, 5)
    columns = write_row(
        sheet,
        rel_offset,
        cell_generator=[
            [
                dev_teams[i].name,
                formats.centered_vertical_text_header_format
                if i != 0 else formats.centered_vertical_text_header_left_border_format
            ] for i in range(len(dev_teams))] + [['Total', formats.centered_vertical_text_header_right_border_format]],
        cell_format=formats.centered_vertical_text_header_format,
        col_width=5
    )

    rel_offset = RelPos(rel_offset, 0, columns + 4)
    columns = write_row(
        sheet,
        rel_offset,
        cell_generator=[
            [
                dev_teams[i].name,
                formats.centered_vertical_text_header_format
                if i != 0 else formats.centered_vertical_text_header_left_border_format
            ] for i in range(len(dev_teams))] + [['Total', formats.centered_vertical_text_header_right_border_format]],
        cell_format=formats.centered_vertical_text_header_format,
        col_width=5
    )

    rel_offset = RelPos(rel_offset, 0, columns)
    columns = write_row(
        sheet,
        rel_offset,
        cell_generator=[
            [
                dev_teams[i].name,
                formats.centered_vertical_text_header_format
                if i != 0 else formats.centered_vertical_text_header_left_border_format
            ] for i in range(len(dev_teams))] + [['Total', formats.centered_vertical_text_header_right_border_format]],
        cell_format=formats.centered_vertical_text_header_format,
        col_width=5
    )

    rel_offset = RelPos(rel_offset, 0, columns)
    write_row(
        sheet,
        rel_offset,
        cell_generator=[
            [
                qa_teams[i].name,
                formats.centered_vertical_text_header_format
                if i != 0 else formats.centered_vertical_text_header_left_border_format
            ] for i in range(len(qa_teams))] + [['Total', formats.centered_vertical_text_header_right_border_format]],
        cell_format=formats.centered_vertical_text_header_format,
        col_width=5
    )

    return Region(RelPos(offset), 3, column_count)


def _add_totals_row(sheet, region: Region, skip_columns: int = 0):
    totals = []
    for column in range(0, region.columns):
        if column == 0:
            totals.append('Total')
        elif column >= skip_columns:
            totals.append(
                f'=SUM('
                f'{RelPos(region.offset, column=column).to_cell()}'
                f':{RelPos(region.offset, region.rows - 1, column).to_cell()}'
                f')'
            )
        else:
            totals.append('')
    offset = RelPos(region.offset, region.rows)
    write_row(sheet, offset, totals, cell_format=formats.bold_total_format)


def _create_dev_activities_table(
    sheet, product_release: ProductRelease, teams: List[Team], offset=Pos()
) -> Tuple[Dict[Team, CellReference], Region]:
    dev_owned_issues = [x for x in product_release.issues if x.owned_by_team.is_dev()]
    if not dev_owned_issues:
        return dict(), Region(offset, 1, 0)

    header_table = _create_release_table_header(sheet, teams, offset)

    for row in range(0, len(dev_owned_issues)):
        issue = dev_owned_issues[row]
        rel_offset = RelPos(header_table.pos_below(), row)
        write_row(
            sheet,
            rel_offset,
            cell_generator=_create_cells_for_issue(issue, teams, rel_offset),
            cell_format=formats.numeric_format
        )

    # totals row
    _add_totals_row(sheet, Region(header_table.pos_below(), len(dev_owned_issues), header_table.columns), 4)

    # adjust column widths
    sheet.set_column(
        offset.column + 1, offset.column + 1,
        max(int(len(x.issue_summary) * 0.75) for x in dev_owned_issues) if dev_owned_issues else 10
    )
    sheet.set_column(
        offset.column, offset.column,
        max(len(x.issue_key) for x in dev_owned_issues) if dev_owned_issues else 10
    )

    # cell references to totals for every team incl dev and qa
    total_cells_by_team = {}
    dev_teams = [x for x in teams if x.is_dev()]
    team_column = header_table.offset.column + 11 + 2 * len(dev_teams)
    for team in dev_teams:
        total_cells_by_team[team] = CellReference(
            Pos(offset.row, team_column, product_release.name), product_release.name
        )
        team_column += 1

    qa_teams = [x for x in teams if x.is_qa()]
    team_column = header_table.offset.column + 12 + 3 * len(dev_teams)
    for team in qa_teams:
        total_cells_by_team[team] = CellReference(
            Pos(offset.row, team_column, product_release.name), f'{product_release.name} checks'
        )
        team_column += 1

    return \
        total_cells_by_team, \
        Region(header_table.offset, header_table.rows + len(dev_owned_issues) + 1, header_table.columns)


def _create_qa_activities_table_header(sheet, qa_teams: List[Team], offset: Pos) -> Region:
    merge_cells(sheet, RelPos(offset, 0, 0), RelPos(offset, 1, 0), 'Key', formats.centered_header_format)
    merge_cells(sheet, RelPos(offset, 0, 1), RelPos(offset, 1, 1), 'Summary', formats.centered_header_format)

    rel_offset = RelPos(offset, 0, 2)
    merge_cells(
        sheet, rel_offset, RelPos(rel_offset, 0, len(qa_teams)),
        'QA effort', formats.centered_header_border_format
    )

    rel_offset = RelPos(rel_offset, 1, 0)
    write_row(
        sheet,
        rel_offset,
        cell_generator=[
            [
                qa_teams[i].name,
                formats.centered_vertical_text_header_format
                if i != 0 else formats.centered_vertical_text_header_left_border_format
            ] for i in range(len(qa_teams))] + [['Total', formats.centered_vertical_text_header_right_border_format]],
        cell_format=formats.centered_vertical_text_header_format,
        col_width=5
    )
    return Region(offset, 2, 3 + len(qa_teams))


def _create_cells_for_qa_issue(issue: Issue, qa_teams: List[Team], offset: Pos) -> List:
    values = [
        [{'url': issue.issue_url, 'string': issue.issue_key}, 'write_url'],
        issue.issue_summary
    ]

    # qa effort
    for i in range(len(qa_teams)):
        team = qa_teams[i]
        values.append([
            seconds_to_man_weeks(issue.remaining_estimates_by_team[team.name].qa_effort or 0),
            formats.numeric_border_left_format if i == 0 else formats.numeric_format
        ])
    # total for qa effort
    values.append([
        f'=SUM('
        f'{RelPos(offset, column=len(values) - len(qa_teams)).to_cell()}'
        f':{RelPos(offset, column=len(values) - 1).to_cell()}'
        f')',
        formats.numeric_border_right_format
    ])

    return values


def _create_qa_activities_table(
    sheet, product_release: ProductRelease, teams: List[Team], offset: Pos
) -> Tuple[Dict[Team, List[CellReference]], Region]:
    qa_owned_issues = [x for x in product_release.issues if x.owned_by_team.is_qa()]
    if not qa_owned_issues:
        return dict(), Region(offset, 1, 0)

    qa_teams = [team for team in teams if team.is_qa()]

    header_table = _create_qa_activities_table_header(sheet, qa_teams, offset)

    total_cells_by_teams = {}
    for row in range(0, len(qa_owned_issues)):
        issue = qa_owned_issues[row]
        rel_offset = RelPos(header_table.pos_below(), row)
        write_row(
            sheet,
            rel_offset,
            cell_generator=_create_cells_for_qa_issue(issue, qa_teams, rel_offset),
            cell_format=formats.numeric_format
        )

        col = 1
        for team in qa_teams:
            if team not in total_cells_by_teams:
                total_cells_by_teams[team] = []

            total_cells_by_teams[team].append(
                CellReference(RelPos(rel_offset, column=col, sheet_name=product_release.name), issue.issue_summary)
            )
            col += 1

    # totals row
    _add_totals_row(sheet, Region(header_table.pos_below(), len(qa_owned_issues), header_table.columns), 2)

    return \
        total_cells_by_teams, \
        Region(header_table.offset, header_table.rows + len(qa_owned_issues) + 1, header_table.columns)


def fill_release_worksheet(
    sheet, product_release: ProductRelease, teams: List[Team]
) -> Dict[Team, List[CellReference]]:

    total_cells_by_dev_team, release_table = _create_dev_activities_table(sheet, product_release, teams)

    total_cells_by_qa_team, _ = _create_qa_activities_table(
        sheet, product_release, teams, RelPos(release_table.pos_below(), 2)
    )

    return merge_dicts(total_cells_by_dev_team, total_cells_by_qa_team)
