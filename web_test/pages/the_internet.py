import typing
from functools import cached_property

import allure
from selene import browser, Element, have, query, be, by

from web_test.assist.allure import report
from web_test.assist.allure.chainable_naming import ChainableNamingElement

CSS = str
XPATH = str
CSS_or_XPATH = CSS | XPATH

R = typing.TypeVar("R", bound="Row")
T = typing.TypeVar("T", bound="Table[Row]")


def uglify_class_name(class_name: str) -> str:
    """ To better show this approach, we need to make locators more production-like. """
    return f'.//*[contains(@class,"MakeThisXPATHMoreRealisticWithSomeFrontendGarbage")' \
           f' or contains(@class,"{class_name}")]'


class BaseElement(ChainableNamingElement):
    """
    This is the Base Element for described elements approach.
    """

    def __str__(self):
        return self.description or self.__class__.__name__


class Modal(BaseElement):
    """
    Since a modal can be presented on a page only in one instance at a time, we don't need to provide a root element
    """
    container_locator = uglify_class_name('modal')
    header_locator = uglify_class_name('modal-title')
    section_locator = uglify_class_name('modal-body')
    footer_locator = uglify_class_name('modal-footer')

    def __init__(self):
        super().__init__()
        self._container = browser.element(self.container_locator)
        self.header: Element = self._container.element(self.header_locator)
        self.section: Element = self._container.element(self.section_locator)
        self.footer = self._container.element(self.footer_locator)
        self.close_button: Element = self.footer.element('p')

    @report.step
    def close(self):
        self.close_button.should(be.enabled).click()


class Row(BaseElement):
    def __init__(self, root: Element, cell_locators: typing.Dict[str, CSS_or_XPATH]):
        """

        Args:
            root ():
            cell_locators (): dictionary with column_name: its_locator pairs.
        """
        super().__init__()
        self.cell_locators = cell_locators
        self._container = root
        self._values: dict = {}
        # alias for an element direct access
        self.body: Element = self._container

    @allure.step('Extracting data from the row')
    def _parse_values(self):
        for field_name, locator in self.cell_locators.items():
            self._container.element(locator).should(have._not_.exact_text(''))
            self._values[field_name] = self._container.element(locator).get(query.text)

    @property
    def values(self) -> dict:
        if not self._values:
            self._parse_values()
        return self._values

    @report.step
    def should_have_values(self, expected_row_values: dict):
        error_message = f"Row doesn't match!\n expected: {expected_row_values}\n presented: {self.values}"
        with allure.step(f'Check that a row has expected values "{expected_row_values.items()}"'):
            assert expected_row_values.items() <= self.values.items(), error_message


class RowWithActions(Row):
    def __init__(self, root: Element, cell_locators: typing.OrderedDict):
        super().__init__(root, cell_locators)
        self.edit_button: Element = self._container.element(by.text("edit"))
        self.delete_button: Element = self._container.element(by.text("delete"))


class Table(BaseElement, typing.Generic[R]):
    def __init__(
            self,
            root: Element,
            locators_dict: typing.Optional[typing.Dict[str, CSS_or_XPATH]],
            header_cell_locator: CSS_or_XPATH = "th",
            row_locator: CSS_or_XPATH = "tr",
            table_body_locator: CSS_or_XPATH = "tbody",
            table_header_locator: CSS_or_XPATH = "thead",
            row_type: typing.Type[R] = Row,
    ):
        """Just a common table class with a variable type of row.

        Args:
            root (): the element where to look for the table
            locators_dict (): dictionary with column_name: its_locator pairs. It may be empty,
                                but then you must implement locators_dict property
            table_header_locator (): css or xpath of a table header
            header_cell_locator (): xpath of a singular cell in a header
            table_body_locator (): css or xpath of a table body (all below a header)
            row_locator (): css or xpath of a singular row
            row_type (): the type of row in a table
        """
        super().__init__()

        self._container = root
        self._cell_locators = locators_dict
        self.body = self._container.element(table_body_locator)
        self.rows = self.body.all(row_locator)
        self.header = self._container.element(table_header_locator)
        self.header_cells = self.header.all(header_cell_locator)
        self.row_type: typing.Type[R] = row_type

    def get_row_count(self) -> int:
        return len(self.rows)

    @property
    def cell_locators(self):
        return self._cell_locators

    @report.step
    def get_row_by_cell_value(self, column_name, value_to_search) -> R:
        filtered_rows = self.rows.by_their(self.cell_locators[column_name], have.text(value_to_search))
        filtered_rows.should(have.size(1))
        return (
            self.row_type(filtered_rows.first, cell_locators=self.cell_locators)
            .as_(f'row_with_"{column_name}"="{value_to_search}"')
            .set_previous_name_chain_element(self)
        )

    @report.step
    def should_have_a_row_with(self, column_name, value_to_search):
        self.get_row_by_cell_value(column_name=column_name, value_to_search=value_to_search)

    def get_row_by_index(self, index) -> R:
        return (
            self.row_type(self.rows[index], cell_locators=self.cell_locators)
            .as_(f"row_number#{index + 1}")
            .set_previous_name_chain_element(self)
        )

    @report.step
    def is_row_presented(self, column_name, value_to_search) -> bool:
        result = self.rows.by_their(self.cell_locators[column_name], have.text(value_to_search))
        return bool(result)


class StandardCellsTable(Table[R]):
    def __init__(
            self,
            root: Element,
            column_names: typing.Tuple[str, ...],
            table_header_locator: CSS_or_XPATH = "thead",
            header_cell_locator: XPATH = ".//th",
            table_body_locator: CSS_or_XPATH = "tbody",
            row_locator: CSS_or_XPATH = ".//tr",
            body_cell_locator: XPATH = ".//td",
            row_type: typing.Type[R] = Row,
    ):
        """
        This table class may be used when all columns in your table have a similar structure. With this class, you can
         only pass column_names, and it will automatically define all cells in a row. It should work even if your table
         has movable columns.

        Args:
            root (): the element where to look for the table
            column_names (): names of columns
            table_header_locator (): css or xpath of a table header
            header_cell_locator (): xpath of a singular cell in a header
            table_body_locator (): css or xpath of a table body (all below a header)
            row_locator (): css or xpath of a singular row
            body_cell_locator (): xpath of a cell in a row
            row_type (): the type of row in a table
        """
        super().__init__(
            root=root,
            locators_dict=None,
            header_cell_locator=header_cell_locator,
            row_locator=row_locator,
            table_body_locator=table_body_locator,
            table_header_locator=table_header_locator,
            row_type=row_type,
        )
        self.column_names = column_names
        self._body_cell_locator = body_cell_locator
        self._header_cell_locator = header_cell_locator

    @cached_property
    @report.step(title_or_callable='preparing cell locators for a table')
    def cell_locators(self) -> typing.Dict[str, CSS_or_XPATH]:
        """
        This function defines cell locators by calculating the number of column with some name in a header.
        Pay attention that it can work only when page is loaded.
        If the order of the columns is changed, you need to clear the cache and recalculate the locators_dict.
        """
        self._container.should(be.present)
        locators_dict = {}
        for column_name in self.column_names:
            locators_dict[column_name] = f"{self._body_cell_locator}[{self._get_column_index_by_name(column_name)}]"
        return locators_dict

    def _get_column_index_by_name(self, column_name):
        return (
                len(
                    self.header.element(f"{self._header_cell_locator}[.//text()='{column_name}']").all(
                        "./preceding-sibling::*"
                    )
                )
                + 1
        )


class BasePage(ChainableNamingElement):
    """
    This is the Base Page for described elements approach
    """

    def __str__(self):
        return self.__class__.__name__

    def __init__(self, url):
        super().__init__()
        self.url = url

    @report.step
    def open(self) -> typing.Self:
        browser.open(self.url)
        return self


class PageWithModal(BasePage):
    def __init__(self):
        super().__init__(url='https://the-internet.herokuapp.com/entry_ad')
        self.modal = Modal()


class PageWithTables(BasePage):
    def __init__(self):
        super().__init__('https://the-internet.herokuapp.com/tables')
        self.table_one: StandardCellsTable[Row] = StandardCellsTable(root=browser.element('#table1'),
                                                                     column_names=(
                                                                         "Last Name", "First Name", "Email", "Due",
                                                                         "Web Site", "Action"))

        # imagine our cells have inconsistent locators, so we have to define them manually
        self.table_two: Table[RowWithActions] = Table(root=browser.element('#table2'),
                                                      locators_dict={
                                                          "Last Name": ".//td[1]",
                                                          "First Name": ".//td[2]",
                                                          "Email": ".//td[3]",
                                                          "Due": ".//td[4]",
                                                          "Web Site": ".//td[5]",
                                                          "Action": ".//td[6]"},
                                                      row_type=RowWithActions)
