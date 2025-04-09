"""
textual app - handles user input, fetches from db and passes to components

ex. user can select a timeframe, will appropriately fetch and route to component
 -> alternative is to have components deal with all of that. will have to see if abstracting it into this layer is feasible/worth it

"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.reactive import reactive
from textual.widget import Widget
from rich.console import RenderableType
from rich.text import Text


class Bar(Widget):
    """Widget that represents a single stacked bar."""

    def __init__(self, row, categories, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.categories = categories

    def render(self) -> Text:
        bar = Text()

        # Render each category in the row
        for category, value in self.row.items():
            color = self.categories.get(category, "white")
            bar_width = round(value * 3)
            bar.append("█" * bar_width, style=color)

        return bar


class Key(Widget):
    """Widget that represents the category key/legend."""

    def __init__(self, categories, **kwargs):
        super().__init__(**kwargs)
        self.categories = categories

    def render(self) -> Text:
        key = Text("\nKey:\n")

        for category, color in self.categories.items():
            key.append(f"{category}: ", style=color)
            key.append(f"[{color}] \n")

        return key


class StackedBarChart(Widget):
    """Widget that combines bars and key into a full chart."""

    def __init__(self, data, categories, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.categories = categories

    def render(self) -> Text:
        chart = Text()

        # Create and add the bars to the chart
        for row in self.data:
            bar_widget = Bar(row=row, categories=self.categories)
            chart.append(str(bar_widget.render()) + "\n")

        # Add the key (legend) below the chart
        key_widget = Key(categories=self.categories)
        chart.append(str(key_widget.render()))

        return chart


class Dashboard(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        chart = StackedBarChart(
            data=[
                {"A": 3, "B": 1},
                {"A": 2, "B": 2},
                {"A": 1, "B": 3},
            ],
            categories={"A": "blue", "B": "green"},
        )
        yield chart
        # yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = Dashboard()
    app.run()
