""" Here is examples of described elements. To get the allure report, add the option --alluredir={dirname}
Then run "allure serve {dirname}" """
from selene import browser, have, be, by

from web_test.pages.the_internet import PageWithModal, PageWithTables


def test_simple_elements():
    """ It is possible to describe elements without any page objects at all """

    modal = browser.open('https://the-internet.herokuapp.com/entry_ad'). \
        element('.modal').as_('better_name_for_a_modal').should(have.text('THIS IS A MODAL WINDOW'))
    # > better_name_for_a_modal: should have text THIS IS A MODAL WINDOW
    modal.element('.modal-title').as_('better_name_for_a_title').should(have.text('THIS IS A MODAL WINDOW'))
    # > better_name_for_a_title: should have text THIS IS A MODAL WINDOW


def test_simple_elements_with_a_chain():
    """ This approach isn't so practical, but it shows how it works on a simple example """

    modal = browser.open('https://the-internet.herokuapp.com/entry_ad'). \
        element('.modal').as_('better_name_for_a_modal').should(have.text('THIS IS A MODAL WINDOW'))
    # > better_name_for_a_modal: should have text THIS IS A MODAL WINDOW
    modal.element('.modal-title'). \
        as_('better_name_for_a_title'). \
        set_previous_name_chain_element(modal). \
        should(have.text('THIS IS A MODAL WINDOW'))
    # note, this time it preserves the naming chain:
    # > better_name_for_a_modal.better_name_for_a_title: should have text THIS IS A MODAL WINDOW


def test_example_with_page_object():
    page = PageWithModal()
    page.open()
    # > PageWithModal: open
    page.modal.section.should(have.text("It's commonly used to encourage a user"))
    # > PageWithModal.modal.section: should have text It's commonly used to encourage a user
    page.modal.section.click()
    # > PageWithModal.modal.section: click
    page.modal.close()
    # > PageWithModal.modal: close
    page.modal.header.should(be.hidden)
    # > PageWithModal.modal.header: should be hidden


def test_example_with_table():
    page = PageWithTables()
    page.open()
    # > PageWithTables: open
    bach_row = page.table_one.get_row_by_cell_value(column_name="Last Name", value_to_search="Bach")
    # > PageWithTables.table_one: preparing cell locators for a table
    # > PageWithTables.table_one: get row by cell value: column name 'Last Name', value to search 'Bach'
    bach_row.should_have_values(
        {"Email": "fbach@yahoo.com",
         "Due": "$51.00"})
    # > PageWithTables.table_one.row_with_"Last Name"="Bach": should have values {'Email': 'fbach@yahoo.com',
    # 'Due': '$51.00'}


def test_index_example():
    page = PageWithTables()
    page.open()
    # > PageWithTables: open
    bach_row = page.table_one.get_row_by_index(1)
    # no extra allure steps for getting row by index

    bach_row.should_have_values(
        {"Email": "fbach@yahoo.com",
         "Due": "$51.00"})
    # > PageWithTables.table_one: preparing cell locators for a table
    # > PageWithTables.table_one.row_number#2: should have values {'Email': 'fbach@yahoo.com', 'Due': '$51.00'}


def test_example_with_table_and_custom_row():
    page = PageWithTables()
    page.open()
    # > PageWithTables: open
    jdoe_row = page.table_two.get_row_by_cell_value(column_name="Email", value_to_search="jdoe@hotmail.com")
    # > PageWithTables.table_two: get row by cell value: column name 'Email', value to search 'jdoe@hotmail.com'
    jdoe_row.delete_button.click()
    # > PageWithTables.table_two.row_with_"Email"="jdoe@hotmail.com".delete_button: click
    # by the way, autocomplete works in the previous step

    page.table_two.rows.should(have._not_.text("jdoe@hotmail.com").each)  # it fails because the tested table has a bug
    # > PageWithTables.table_two.rows: each has no (text jdoe@hotmail.com)


""" Issues that cannot be solved easily """


def test_chain_elements_is_not_preserved():
    # When Selene creates a new element the naming chain is not preserved
    page = PageWithModal()
    page.open()
    # > PageWithModal: open

    # Imagine we want to define an element by a text:
    page.modal.footer.element(by.text("Close")).click()
    # > element('xpath', './/*[contains(@class,"MakeThisXPATHMoreRealisticWithSomeFrontendGarbage") or contains(@class,"modal")]').element('xpath', './/*[contains(@class,"MakeThisXPATHMoreRealisticWithSomeFrontendGarbage") or contains(@class,"modal-footer")]').element('xpath', './/*[text()[normalize-space(.) = concat("", "Close")]]'): click

    # to fix this issue, we have to define all elements somewhere in or Pages/Elements. It may be not convenient,
    # especially for Selene's filtering methods.


def test_chain_elements_workaround():
    """ ofcourse, it is the least convenient method """
    page = PageWithModal()
    page.open()
    # > PageWithModal: open
    modal_footer = page.modal.footer
    modal_footer.element(by.text("Close")). \
        as_("close button"). \
        set_previous_name_chain_element(modal_footer). \
        click()
    # > PageWithModal.modal.footer.close button: click
