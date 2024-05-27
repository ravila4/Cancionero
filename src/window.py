from typing import List

import html2text
from gi.repository import Adw
from gi.repository import Gtk
from .ug import ug_search, ug_tab, SearchResult


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
        self.search_entry.get_style_context().add_class("search-entry-title")

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
        self.search_entry.set_text(self.current_result)
        song_url = self.get_url_from_label(self.current_result)
        song_detail = ug_tab(song_url)
        self.display_song_detail(song_detail)

    def display_song_detail(self, song_detail):
        # TODO Add vertical and horizontal scroll bars
        buffer = self.song_detail_textview.get_buffer()
        plain_text = html2text.html2text(song_detail.tab)
        buffer.set_text(plain_text)
        self.content_stack.set_visible_child_name("song_detail")
        self.back_button.set_sensitive(
            True
        )  # Enable back button when viewing song details
        self.forward_button.set_sensitive(
            False
        )  # Disable forward button when on song details page

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
