import typing

from selene.core.entity import WaitingEntity

T = typing.TypeVar("T", bound="ChainableNamingElement")


class ChainableNamingElement:
    """
    This class makes its children store their attribute names as a description and a link to a parent element.
    Then it can be used to resolve chainable names like: "PreviewCodingLabPage.sidebar.show_hints_button"

    To use it, just inherit from this class (BasePage or BaseElement), and create a nested structure of attributes.
    And then call get_full_path() for any nested attribute.

    This class also works with Selene's elements, but it requires monkey patching.
    """

    def __init__(self):
        self.description = ""
        self.previous_name_chain_element = None

    def __setattr__(self, key, value):
        if isinstance(value, WaitingEntity):
            if not getattr(value, "description", ""):
                value.as_(key)
            value.previous_name_chain_element = self
        elif isinstance(value, ChainableNamingElement) and key != "previous_name_chain_element":
            if not getattr(value, "description", ""):
                value.description = key
            value.previous_name_chain_element = self
        super().__setattr__(key, value)

    def __str__(self):
        return self.description or self.__class__.__name__

    def get_full_path(self):
        result = ".".join(self.resolve_name())
        return result

    def resolve_name(self) -> list:
        if self.previous_name_chain_element:
            name = self.previous_name_chain_element.resolve_name()
        else:
            name = []
        name.append(str(self))
        return name

    def as_(self: T, element_name: str) -> T:
        self.description = element_name
        return self

    def set_previous_name_chain_element(self: T, previous_element: T | WaitingEntity) -> T:
        self.previous_name_chain_element = previous_element
        return self
