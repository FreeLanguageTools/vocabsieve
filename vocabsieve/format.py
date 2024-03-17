from markdown import markdown


def markdown_nop(s: str) -> str:
    return markdown(s.replace("\n", "\n\n").replace(".", r"\.")).\
        replace("<p>", "<br>").\
        replace("</p>", "").\
        removeprefix("<br>")
