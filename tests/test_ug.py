import sys
from pathlib import Path

import pytest

# Add the parent directory of both src and tests to sys.path
project_root = Path(__file__).resolve().parent.parent
if project_root not in sys.path:
    sys.path.append(str(project_root))

from src.ug import SongDetail  # noqa: E402
from src.ast import (
    LineNode,
    ChordNode,
    SpacerNode,
    SectionHeaderNode,
    CommentNode,
    TextNode,
)


class MockSongDetail(SongDetail):
    def __init__(self, tab):
        self.tab = tab


@pytest.fixture
def make_song_detail():
    def _make_song_detail(tab_string):
        mock_song = MockSongDetail(tab_string)
        return mock_song

    return _make_song_detail


def test_parse_tab_to_ast(make_song_detail):
    tab = "[ch]C[/ch]                 [ch]E[/ch]\nLife could be so handsome"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 2  # Two lines
    assert isinstance(ast.children[0], LineNode)
    assert isinstance(ast.children[1], LineNode)
    assert len(ast.children[0].children) == 3
    assert isinstance(ast.children[0].children[0], ChordNode)
    assert isinstance(ast.children[0].children[1], SpacerNode)
    assert isinstance(ast.children[0].children[2], ChordNode)
    assert ast.children[0].children[0].name == "C"
    assert ast.children[0].children[1].length == 17
    assert ast.children[0].children[2].name == "E"
    assert len(ast.children[1].children) == 1
    assert isinstance(ast.children[1].children[0], TextNode)
    assert ast.children[1].children[0].text == "Life could be so handsome"


def test_parse_tab_to_ast_with_section_header(make_song_detail):
    tab = "[Verse 2]\n[ch]C[/ch]            [ch]E[/ch]\nLife could be so handsome"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 3
    tab = "[Verse 2]\n[ch]C[/ch]            [ch]E[/ch]\nLife could be so handsome"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 3
    assert isinstance(ast.children[0], LineNode)
    assert isinstance(ast.children[1], LineNode)
    assert isinstance(ast.children[2], LineNode)
    assert isinstance(ast.children[0].children[0], SectionHeaderNode)
    assert ast.children[0].children[0].name == "[Verse 2]"
    assert len(ast.children[1].children) == 3
    assert isinstance(ast.children[1].children[0], ChordNode)
    assert isinstance(ast.children[1].children[1], SpacerNode)
    assert isinstance(ast.children[1].children[2], ChordNode)
    assert ast.children[1].children[0].name == "C"
    assert ast.children[1].children[1].length == 12
    assert ast.children[1].children[2].name == "E"
    assert len(ast.children[2].children) == 1
    assert isinstance(ast.children[2].children[0], TextNode)
    assert ast.children[2].children[0].text == "Life could be so handsome"


def test_parse_tab_to_ast_with_comment(make_song_detail):
    tab = "(This is a comment)"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 1
    assert isinstance(ast.children[0], LineNode)
    assert len(ast.children[0].children) == 1
    assert isinstance(ast.children[0].children[0], CommentNode)
    assert ast.children[0].children[0].comment == "(This is a comment)"


def test_parse_tab_to_ast_joined_chords(make_song_detail):
    """Intros sometimes have several chords with single spaces
    and or dashes between them
    """
    tab = "[ch]E[/ch] - [ch]Emaj7[/ch] x2 [ch]G#m[/ch] - [ch]A[/ch] - [ch]C#m[/ch]"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 1
    assert isinstance(ast.children[0], LineNode)
    assert len(ast.children[0].children) == 9
    assert isinstance(ast.children[0].children[0], ChordNode)
    assert isinstance(ast.children[0].children[1], TextNode)
    assert isinstance(ast.children[0].children[2], ChordNode)
    assert isinstance(ast.children[0].children[3], TextNode)
    assert isinstance(ast.children[0].children[4], ChordNode)
    assert isinstance(ast.children[0].children[5], TextNode)
    assert isinstance(ast.children[0].children[6], ChordNode)
    assert isinstance(ast.children[0].children[7], TextNode)
    assert isinstance(ast.children[0].children[8], ChordNode)
    assert ast.children[0].children[0].name == "E"
    assert ast.children[0].children[2].name == "Emaj7"
    assert ast.children[0].children[4].name == "G#m"
    assert ast.children[0].children[6].name == "A"
    assert ast.children[0].children[8].name == "C#m"
    assert ast.children[0].children[1].text == " - "
    assert ast.children[0].children[3].text == " x2 "
    assert ast.children[0].children[5].text == " - "
    assert ast.children[0].children[7].text == " - "


def test_parse_tab_to_ast_with_multiple_sections(make_song_detail):
    tab = "\n\n[Verse](all verses follow same progression)\n[ch]A[/ch]"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 4
    assert isinstance(ast.children[0], LineNode)
    assert isinstance(ast.children[1], LineNode)
    assert isinstance(ast.children[2], LineNode)
    assert isinstance(ast.children[3], LineNode)
    assert len(ast.children[0].children) == 0
    assert len(ast.children[1].children) == 0
    assert len(ast.children[2].children) == 2
    assert len(ast.children[3].children) == 1
    assert isinstance(ast.children[2].children[0], SectionHeaderNode)
    assert isinstance(ast.children[2].children[1], CommentNode)
    assert isinstance(ast.children[3].children[0], ChordNode)


def test_parse_tab_to_ast_with_return_char(make_song_detail):
    tab = "\n[Verse 1]\r\n"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 3
    assert isinstance(ast.children[0], LineNode)
    assert isinstance(ast.children[1], LineNode)
    assert len(ast.children[1].children) == 1
    assert isinstance(ast.children[1].children[0], SectionHeaderNode)
    assert ast.children[1].children[0].name == "[Verse 1]"

    
def test_parse_tab_to_ast_trailing_space(make_song_detail):
    tab = "[Verse 1] \n"
    song = make_song_detail(tab)
    ast = song.parse_tab_to_ast()
    assert len(ast.children) == 2
    assert isinstance(ast.children[0], LineNode)
    assert isinstance(ast.children[1], LineNode)
    assert len(ast.children[0].children) == 1
    assert isinstance(ast.children[0].children[0], SectionHeaderNode)
    assert ast.children[0].children[0].name == "[Verse 1]"
