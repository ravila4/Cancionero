from typing import List

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
import json
import re

from dataclasses import dataclass, field

from .ast import (
    ASTNode,
    LineNode,
    ChordNode,
    SpacerNode,
    SectionHeaderNode,
    CommentNode,
    TextNode,
)


@dataclass
class SearchResult:
    artist_name: str
    song_name: str
    tab_url: str
    artist_url: str
    _type: str
    version: int
    votes: int
    rating: float

    def __init__(self, data: str):
        self.artist_name = data["artist_name"]
        self.song_name = data["song_name"]
        self.tab_url = urlparse(data["tab_url"]).path
        self.artist_url = data["artist_url"]
        self._type = data["type"]
        self.version = data["version"]
        self.votes = int(data["votes"])
        self.rating = round(data["rating"], 1)

    def __repr__(self):
        return f"{self.artist_name} - {self.song_name} (ver {self.version}) ({self._type} {self.rating}/5 - {self.votes} votes)"


@dataclass
class SongDetail:
    tab: str
    artist_name: str
    song_name: str
    version: int
    difficulty: str
    capo: str
    tuning: str
    tab_url: str
    versions: list[SearchResult] = field(default_factory=list)

    def __init__(self, data):
        if __name__ == "__main__":
            with open("test.json", "w") as f:
                json.dump(data, f)
        self.tab = data["store"]["page"]["data"]["tab_view"]["wiki_tab"]["content"]
        self.artist_name = data["store"]["page"]["data"]["tab"]["artist_name"]
        self.song_name = data["store"]["page"]["data"]["tab"]["song_name"]
        self.version = int(data["store"]["page"]["data"]["tab"]["version"])
        self._type = data["store"]["page"]["data"]["tab"]["type"]
        self.rating = int(data["store"]["page"]["data"]["tab"]["rating"])
        self.difficulty = data["store"]["page"]["data"]["tab_view"]["ug_difficulty"]
        self.applicature = data["store"]["page"]["data"]["tab_view"]["applicature"]
        self.chords = []
        self.fingers_for_strings = []
        if isinstance(data["store"]["page"]["data"]["tab_view"]["meta"], dict):
            self.capo = data["store"]["page"]["data"]["tab_view"]["meta"].get("capo")
            _tuning = data["store"]["page"]["data"]["tab_view"]["meta"].get("tuning")
            self.tuning = f"{_tuning['value']} ({_tuning['name']})" if _tuning else None
        self.tab_url = data["store"]["page"]["data"]["tab"]["tab_url"]
        self.versions = []
        for version in data["store"]["page"]["data"]["tab_view"]["versions"]:
            self.versions.append(SearchResult(version))
        self.fix_tab()

    def __repr__(self):
        return f"{self.artist_name} - {self.song_name}"

    def parse_tab_to_ast(self):
        """
        Parse the tab string into an AST to annotate:
        - Chords: [ch]C[/ch]
        - Section headers: [Header]
        - Comments: (Comment)
        - Spacers: 2 or more space characters between chords
        - Text: any other text
        """
        root = ASTNode()
        lines = self.tab.replace("\r", "").split("\n")

        for line in lines:
            line_node = LineNode()
            root.add_child(line_node)
            chord_pattern = re.compile(
                r"\[ch\](?P<chord>[A-Ga-g](#|b)?[^[/]*(?:/[^[/]+)?)\[/ch\]"
            )
            last_end = 0

            for chord_match in chord_pattern.finditer(line):
                if chord_match.start() > last_end:
                    # Parse any text before the chord
                    leading_text = line[last_end : chord_match.start()]
                    # Find any non-space characters in the leading text, allowing one space between words
                    non_space_pattern = re.compile(r"\s?(?:(?!\s{2,})\S+\s*)+")
                    last_end_lt = 0
                    for non_space_match in non_space_pattern.finditer(leading_text):
                        # Check if match is a section header
                        if non_space_match.group().startswith(
                            "["
                        ) and non_space_match.group().endswith("]"):
                            # Add any spaces before the section header
                            if non_space_match.start() > last_end_lt:
                                spacer = SpacerNode(
                                    non_space_match.start() - last_end_lt
                                )  # Length of the spacer
                                line_node.add_child(spacer)
                            section_header = SectionHeaderNode(non_space_match.group())
                            line_node.add_child(section_header)
                            last_end_lt = non_space_match.end()
                        # Check if match is a comment
                        elif non_space_match.group().startswith(
                            "("
                        ) and non_space_match.group().endswith(")"):
                            # Add any spaces before the comment
                            if non_space_match.start() > last_end_lt:
                                spacer = SpacerNode(
                                    non_space_match.start() - last_end_lt
                                )  # Length of the spacer
                                line_node.add_child(spacer)
                            comment = CommentNode(non_space_match.group())
                            line_node.add_child(comment)
                            last_end_lt = non_space_match.end()
                        else:
                            # Add any spaces before the text
                            if non_space_match.start() > last_end_lt:
                                spacer = SpacerNode(non_space_match.start() - last_end_lt)
                                line_node.add_child(spacer)
                            # Add the text node
                            text = TextNode(non_space_match.group())
                            line_node.add_child(text)
                        last_end_lt = non_space_match.end()
                    # Add any spaces before the chord
                    if chord_match.start() > last_end + last_end_lt:
                        spacer = SpacerNode(chord_match.start() - last_end)
                        line_node.add_child(spacer)
                # Add the chord node
                chord = chord_match.group("chord")
                chord_node = ChordNode(chord)
                line_node.add_child(chord_node)
                last_end = chord_match.end()
            # Parse any text after the last chord or if there are no chords
            if last_end < len(line):
                trailing_text = line[last_end:]
                # Find any non-space characters in the trailing text, allowing one space between words
                non_space_pattern = re.compile(r"\s?(?:(?!\s{2,})\S+\s*)+")
                last_end_tr = 0
                for non_space_match in non_space_pattern.finditer(trailing_text):
                    # Check if match is a section header
                    if non_space_match.group().startswith(
                        "["
                    ) and non_space_match.group().endswith("]"):
                        # Add any spaces before the section header
                        if non_space_match.start() > last_end_tr:
                            spacer = SpacerNode(non_space_match.start() - last_end_tr)
                            line_node.add_child(spacer)
                        section_header = SectionHeaderNode(non_space_match.group())
                        line_node.add_child(section_header)
                        last_end_tr = non_space_match.end()
                    # Check if match is a comment
                    elif non_space_match.group().startswith(
                        "("
                    ) and non_space_match.group().endswith(")"):
                        # Add any spaces before the comment
                        if non_space_match.start() > last_end_tr:
                            spacer = SpacerNode(non_space_match.start() - last_end_tr)
                            line_node.add_child(spacer)
                        comment = CommentNode(non_space_match.group())
                        line_node.add_child(comment)
                        last_end_tr = non_space_match.end()
                    else:
                        # Add any spaces before the text
                        if non_space_match.start() > last_end_tr:
                            spacer = SpacerNode(non_space_match.start() - last_end_tr)
                            line_node.add_child(spacer)
                        # Add the text node
                        text = TextNode(non_space_match.group())
                        line_node.add_child(text)
                    last_end = non_space_match.end()
        return root

    def fix_tab(self):
        tab = self.tab
        # (?P<root>[A-Ga-g](#|b)?) : Chord root is any letter A - G with an optional sharp or flat at the end
        # (?P<quality>[^[/]+)?  : Chord quality is anything after the root, but before the `/` for the base note
        # (?P<bass>/[A-Ga-g](#|b)?)? :  Chord bass is anything after the root, including parens in the case of 'm(maj7)'
        chord_pattern = re.compile(
            r"\[ch\](?P<root>[A-Ga-g](#|b)?)(?P<quality>[^[/]+)?(?P<bass>/[A-Ga-g](#|b)?)?\[\/ch\]"
        )
        self.chords = []
        self.chord_positions = []

        def parse_chord(match):
            root = match.group("root")
            quality = match.group("quality") if match.group("quality") else ""
            bass = match.group("bass")[1:] if match.group("bass") else ""
            full_chord = root + quality + bass
            self.chords.append(full_chord)
            self.chord_positions.append((match.start(), match.end()))
            return full_chord

        # tab = chord_pattern.sub(parse_chord, tab)
        self.tab = tab


def ug_search(value: str) -> List[SearchResult]:
    resp = requests.get(
        f"https://www.ultimate-guitar.com/search.php?search_type=title&value={quote(value)}"
    )
    bs = BeautifulSoup(resp.text, "html.parser")
    # data can be None
    data = bs.find("div", {"class": "js-store"})
    # KeyError
    data = data.attrs["data-content"]
    data = json.loads(data)
    results = data["store"]["page"]["data"]["results"]
    ug_results = []
    for result in results:
        _type = result.get("type")
        if _type and _type != "Pro":
            s = SearchResult(result)
            ug_results.append(s)
            # print(s)
    # print(json.dumps(data, indent=4))
    return ug_results


def get_chords(s: SongDetail):
    if s.applicature is None:
        return dict(), dict()

    chords = {}
    fingerings = {}

    for chord in s.applicature:
        for chord_variant in s.applicature[chord]:
            frets = chord_variant["frets"]
            min_fret = min(frets)
            max_fret = max(frets)
            possible_frets = list(range(min_fret, max_fret + 1))
            variants_temp = {
                possible_fret: [1 if b == possible_fret else 0 for b in frets][::-1]
                for possible_fret in possible_frets
                if possible_fret > 0
            }

            variants = dict()
            found = False
            for fret, fingers in variants_temp.items():
                try:
                    if not found and fingers.index(1) >= 0:
                        found = True
                except ValueError:
                    ...

                if found:
                    variants[fret] = fingers

            if not len(variants):
                continue
            while len(variants) < 6:
                variants[max(variants) + 1] = [0] * 6

            variant_strings_pressed = [*variants.values()]
            variant_strings_pressed = [sum(x) for x in zip(*variant_strings_pressed)]
            unstrummed_strings = [int(not bool(y)) for y in variant_strings_pressed]

            fingering_for_variant = []
            for finger, x in zip(chord_variant["fingers"][::-1], unstrummed_strings):
                fingering_for_variant.append("x" if x else finger)
            fingering_for_variant = fingering_for_variant

            if chord not in chords:
                chords[chord] = []
                fingerings[chord] = []
            chords[chord].append(variants)
            fingerings[chord].append(fingering_for_variant)

    return chords, fingerings


def ug_tab(url_path: str):
    resp = requests.get("https://tabs.ultimate-guitar.com/" + url_path)
    bs = BeautifulSoup(resp.text, "html.parser")
    # data can be None
    data = bs.find("div", {"class": "js-store"})
    data = data.attrs["data-content"]
    data = json.loads(data)
    s = SongDetail(data)
    s.chords, s.fingers_for_strings = get_chords(s)
    print(json.dumps(data, indent=4))
    return s
