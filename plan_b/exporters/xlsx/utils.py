from xlsxwriter.utility import xl_rowcol_to_cell


class Pos:

    def __init__(self, row: int = 0, column: int = 0, sheet_name: str = None):
        self.row: int = row
        self.column: int = column
        self.sheet_name = sheet_name

    def to_cell(self) -> str:
        pos = xl_rowcol_to_cell(self.row, self.column)
        if self.sheet_name:
            pos = f'\'{self.sheet_name}\'!{pos}'
        return pos


class RelPos(Pos):

    def __init__(self, offset: Pos, row: int = 0, column: int = 0, sheet_name: str = None):
        super().__init__(offset.row + row, offset.column + column, sheet_name)


class Region:

    def __init__(self, offset: Pos = Pos(0, 0), rows: int = 0, columns: int = 0):
        self.offset: Pos = offset
        self.columns: int = columns
        self.rows: int = rows

    def pos_below(self) -> Pos:
        return RelPos(self.offset, self.rows, 0)


def write_row(
    sheet,
    offset: Pos,
    cell_generator=None,
    cell_func=None,
    col_count: int = 0,
    cell_format=None,
    col_width=None
) -> int:
    """
    Universal function for writing a row of values to worksheet
    :param sheet: worksheet where to write values
    :param offset: position of first cell of a row
    :param cell_generator: generator that returns cell values
    :param cell_func: function that returns value for the cell with given column index and value from cell_generator
    :param col_count: number of cells (columns) to write
    :param cell_format: format of cells being written
    :param col_width: typical cell width
    :return: number of cells written
    """
    column = offset.column
    if not cell_generator:
        if col_count is not None:
            cell_generator = range(0, col_count)
        else:
            raise RuntimeError('either cell_generator or col_count must be not None')

    for item in cell_generator:

        cell_write_func = sheet.write
        current_cell_format = None
        if isinstance(item, list):
            if isinstance(item[0], dict):
                value, cell_write_func_name = item[0], item[1]
                cell_write_func = getattr(sheet, cell_write_func_name)
            else:
                value, current_cell_format = item[0], item[1]
        else:
            value = item
            current_cell_format = cell_format

        cell_value = cell_func(column, value) if cell_func else value
        if isinstance(cell_value, str) and cell_value.startswith('='):
            sheet.write_formula(offset.row, column, cell_value, current_cell_format)
        else:
            if isinstance(cell_value, dict):
                cell_write_func(offset.row, column, **cell_value)
            else:
                cell_write_func(offset.row, column, cell_value, current_cell_format)
        column += 1

    columns_written = column - offset.column

    if col_width is not None:
        sheet.set_column(offset.column, offset.column + columns_written - 1, width=col_width)

    return columns_written


def merge_cells(sheet, start: Pos, end: Pos, value, cell_format=None, width=None):
    sheet.merge_range(start.row, start.column, end.row, end.column, value, cell_format=cell_format)
    if width is not None:
        sheet.set_column(start.column, start.column, width=width)
    return start.row, start.column


def merge_dicts(d1: dict, d2: dict) -> dict:
    result = {}
    for k, v in d1.items():
        result[k] = [v] if not isinstance(v, list) else v
        other_v = d2.get(k, [])
        if isinstance(other_v, list):
            result[k] += other_v
        else:
            result[k].append(other_v)

    for k, v in [(x, y) for x, y in d2.items() if x not in d1.keys()]:
        result[k] = [v] if not isinstance(v, list) else v

    return result
