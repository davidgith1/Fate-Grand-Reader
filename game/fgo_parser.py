import re
import shlex

TAG_REGEX = re.compile(r"\[([^\]]+)\]")
PAGE_TOKENS = {"page", "k", "nopage", "newline"}
LINE_BREAK_TAGS = {"r", "sr"}
SPEAKER_MARKERS = ("\uff20", "@", "\xef\xbc\xa0")
CHOICE_MARKERS = ("\uff1f", "?", "\xef\xbc\x9f")
FULLWIDTH_COLONS = ("\uff1a", "\xef\xbc\x9a")
MUSIC_MARKERS = ("\u266a", "\u266b", "\xe2\x99\xaa", "\xe2\x99\xac")


def _strip_script_tags(text: str) -> tuple[str, dict[str, str]]:
    tags: dict[str, str] = {}

    def replace_tag(match: re.Match[str]) -> str:
        token = match.group(1).strip()
        if not token:
            return ""

        if "=" in token:
            key, value = token.split("=", 1)
            tag_key = key.strip().lower()
            tags[tag_key] = value.strip()
        else:
            tag_key = token.strip().lower()
            tags[tag_key] = ""

        if tag_key in LINE_BREAK_TAGS:
            return "\n"

        return ""

    cleaned = TAG_REGEX.sub(replace_tag, text)
    return cleaned.strip(), tags


def _parse_dialogue_line(line: str) -> tuple[str, str]:
    content = line[1:].strip()
    speaker = content
    message = ""
    for colon in FULLWIDTH_COLONS + (":",):
        if colon in content:
            speaker, message = content.split(colon, 1)
            break
    return speaker.strip(), message.strip()


def _parse_command_node(token: str):
    try:
        token_parts = shlex.split(token)
    except ValueError:
        token_parts = token.split()
    command = token_parts[0].lower() if token_parts else ""
    if command == "scene" and len(token_parts) >= 2:
        return {
            "type": "scene",
            "scene_id": token_parts[1],
            "tags": {"scene": token},
        }
    if command == "bgm" and len(token_parts) >= 2:
        return {"type": "bgm", "name": token_parts[1], "tags": {"bgm": token}}
    if command in ("bgmstop", "soundstopall"):
        return {"type": "audio_stop", "tags": {command: token}}
    if command == "charaset" and len(token_parts) >= 4:
        return {
            "type": "chara_set",
            "slot": token_parts[1],
            "chara_id": token_parts[2],
            "position": token_parts[3],
            "name": token_parts[4] if len(token_parts) >= 5 else "",
            "tags": {"charaSet": token},
        }
    if command == "charaface" and len(token_parts) >= 3:
        return {
            "type": "chara_face",
            "slot": token_parts[1],
            "face": token_parts[2],
            "tags": {"charaFace": token},
        }
    if command == "charafadein" and len(token_parts) >= 2:
        return {
            "type": "chara_show",
            "slot": token_parts[1],
            "position": token_parts[3] if len(token_parts) >= 4 else None,
            "tags": {"charaFadein": token},
        }
    if command == "charafadeout" and len(token_parts) >= 2:
        return {
            "type": "chara_hide",
            "slot": token_parts[1],
            "tags": {"charaFadeout": token},
        }
    return None


def parse_script_text(raw_text: str) -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = []
    if not raw_text:
        return nodes

    current_speaker = "Narrator"
    current_speaker_slot = None
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            token = line[1:-1].strip()
            token_lower = token.lower()
            command_node = _parse_command_node(token)
            if command_node:
                nodes.append(command_node)
                continue
            if token_lower in PAGE_TOKENS:
                continue

        line, tags = _strip_script_tags(line)
        if not line:
            if tags:
                nodes.append({"type": "metadata", "tags": tags})
            continue
        if line.startswith(("$", "\uff04")):
            nodes.append({"type": "metadata", "tags": {"script_label": line}})
            continue

        if line.startswith(SPEAKER_MARKERS):
            speaker_slot, text = _parse_dialogue_line(line)
            current_speaker_slot = speaker_slot or None
            current_speaker = text or speaker_slot or "Narrator"
            nodes.append(
                {
                    "type": "metadata",
                    "tags": {
                        "speaker": current_speaker,
                        "speaker_slot": current_speaker_slot or "",
                    },
                }
            )
            continue

        if line.startswith(CHOICE_MARKERS):
            choice_text = line[1:].strip()
            if choice_text:
                nodes.append(
                    {
                        "type": "choice",
                        "text": choice_text,
                        "tags": tags,
                    }
                )
            continue

        if line.startswith(MUSIC_MARKERS):
            line = line.lstrip("".join(MUSIC_MARKERS)).strip()

        nodes.append(
            {
                "type": "dialogue",
                "speaker": current_speaker,
                "speaker_slot": current_speaker_slot,
                "text": line,
                "tags": tags,
            }
        )

    return nodes
