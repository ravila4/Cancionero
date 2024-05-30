import re
from typing import List

from gi.repository import Adw, Gtk, Pango

from .ast import (
    ASTNode,
    ChordNode,
    CommentNode,
    LineNode,
    SectionHeaderNode,
    SpacerNode,
    TextNode,
)
from .ug import SearchResult, SongDetail, ug_search, ug_tab


@Gtk.Template(resource_path="/com/github/ravila4/Cancionero/window.ui")
class CancioneroWindow(Adw.ApplicationWindow):
    __gtype_name__ = "CancioneroWindow"

    back_button = Gtk.Template.Child()
    forward_button = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    results_listbox = Gtk.Template.Child()
    content_stack = Gtk.Template.Child()
    song_detail_textview = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_entry.connect("activate", self.on_search_entry_activate)
        self.results_listbox.connect("row-activated", self.on_result_clicked)
        self.back_button.connect("clicked", self.on_back_button_clicked)
        self.forward_button.connect("clicked", self.on_forward_button_clicked)

        self.buffer = self.song_detail_textview.get_buffer()
        # Tags for the text view
        self.chord_tag = self.buffer.create_tag(
            "chord", foreground="blue", weight=Pango.Weight.BOLD
        )
        self.hidden_tag = self.buffer.create_tag("hidden", invisible=True)
        self.section_header_tag = self.buffer.create_tag(
            "section_header", foreground="gray"
        )
        self.comment_tag = self.buffer.create_tag("comment", foreground="gray")

    def on_search_entry_activate(self, widget):
        search_query = self.search_entry.get_text()
        self.search_songs(search_query)

    def search_songs(self, query):
        # TODO: Rather than store the results to in the class instance, we could implement a disk cache
        self.content_stack.set_visible_child_name("search_results")
        self.results = ug_search(query)
        self.display_results(self.results)

    def display_results(self, results: List[SearchResult]):
        self.results_listbox.remove_all()  # Clear the list box
        for result in results:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(
                label=f"{result.artist_name} - {result.song_name} (ver {result.version})"
            )
            row.set_child(label)
            row.connect("activate", self.on_result_clicked, result)
            self.results_listbox.append(row)
            self.back_button.set_sensitive(False)
            self.forward_button.set_sensitive(False)

    def get_url_from_label(self, label: str):
        # TODO: We probably want to retrieve the url from a cache
        for result in self.results:
            if (
                label
                == f"{result.artist_name} - {result.song_name} (ver {result.version})"
            ):
                return result.tab_url

    def on_result_clicked(self, listbox, row):
        self.current_result = row.get_child().get_label()
        # TODO: Set the text in a title label instead, and hide the search bar.
        # add a search button to switch back and forth.
        self.search_entry.set_text(self.current_result)
        song_url = self.get_url_from_label(self.current_result)
        song_detail = ug_tab(song_url)
        self.display_song_detail(song_detail)

    def display_song_detail(self, song_detail: SongDetail):
        # clear buffer
        self.buffer.set_text("")
        # parse the tab into a syntax tree
        ast = song_detail.parse_tab_to_ast()
        self.apply_formatting_from_ast(self.buffer, ast)

        self.content_stack.set_visible_child_name("song_detail")
        self.back_button.set_sensitive(
            True
        )  # Enable back button when viewing song details
        self.forward_button.set_sensitive(
            False
        )  # Disable forward button when on song details

    def apply_formatting_from_ast(self, buffer, ast):
        def apply_formatting(node, start_iter):
            if isinstance(node, TextNode):
                buffer.insert(start_iter, node.text)
            elif isinstance(node, ChordNode):
                buffer.insert_with_tags_by_name(start_iter, "[ch]", "hidden")
                chord_start_iter = buffer.get_end_iter()
                buffer.insert_with_tags(chord_start_iter, node.name, self.chord_tag)
                buffer.insert_with_tags_by_name(
                    buffer.get_end_iter(), "[/ch]", "hidden"
                )
            elif isinstance(node, SectionHeaderNode):
                buffer.insert_with_tags_by_name(start_iter, node.name, "section_header")
            elif isinstance(node, CommentNode):
                buffer.insert_with_tags_by_name(start_iter, node.comment, "comment")
            elif isinstance(node, SpacerNode):
                buffer.insert(start_iter, " " * node.length)
            elif isinstance(node, LineNode) or isinstance(node, ASTNode):
                for child in node.children:
                    apply_formatting(child, buffer.get_end_iter())
                buffer.insert(buffer.get_end_iter(), "\n")

        apply_formatting(ast, buffer.get_start_iter())

    def on_back_button_clicked(self, widget):
        self.content_stack.set_visible_child_name("search_results")
        self.search_entry.set_text("")  # Clear the search entry
        self.back_button.set_sensitive(
            False
        )  # Disable back button when on search results page
        self.forward_button.set_sensitive(
            True
        )  # Enable forward button when going back to search results

    def on_forward_button_clicked(self, widget):
        self.content_stack.set_visible_child_name("song_detail")
        self.search_entry.set_text(self.current_result)
        self.back_button.set_sensitive(
            True
        )  # Enable back button when viewing song details
        self.forward_button.set_sensitive(
            False
        )  # Disable forward button when on song details page
