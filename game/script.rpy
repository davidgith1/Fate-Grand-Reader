define n = Character(None)
define config.screen_width = 1280
define config.screen_height = 720
default active_war = None
default war_list = []
default war_load_error = None
default selected_war_id = 0
default current_background_path = None
default current_scene_id = None
default current_characters = []
default current_chara_defs = {}
default current_speaker_name = None
default current_speaker_slot = None
default backlog = []
default current_reader_marker = None
default resume_marker = None
default menu_notice = ""
define SPEED = 0.01
image running_fou:
    "gui/loadIcon (1).png"
    SPEED
    "gui/loadIcon (2).png"
    SPEED
    "gui/loadIcon (3).png"
    SPEED
    "gui/loadIcon (4).png"
    SPEED
    repeat

init python:
    from atlas_api import AtlasAPI
    
    def get_api():
        if not hasattr(renpy.store, "_atlas_api") or renpy.store._atlas_api is None:
            renpy.store._atlas_api = AtlasAPI()
        return renpy.store._atlas_api

    def renpy_literal(value):
        return str(value).replace("[", "[[").replace("{", "{{")

    def normalize_choice_text(text):
        text = str(text or "").strip()
        text = text.lstrip("0123456789")
        text = text.lstrip(":\uff1a").strip()
        return text

    def collect_choice_options(nodes, start_idx):
        choices = []
        idx = start_idx
        while idx < len(nodes) and nodes[idx].get("type") == "choice":
            text = normalize_choice_text(nodes[idx].get("text"))
            if text and text not in ("!", "\uff01"):
                choices.append(text)
            idx += 1
        return choices, idx

    def record_dialogue(speaker, line):
        entry = {"speaker": speaker or "", "line": line or ""}
        renpy.store.backlog.append(entry)
        if len(renpy.store.backlog) > 200:
            renpy.store.backlog = renpy.store.backlog[-200:]

    def slot_xalign(slot, position=None):
        value = position
        if value is None:
            value = renpy.store.current_chara_defs.get(slot, {}).get("position")
        try:
            pos = int(value)
        except Exception:
            pos = 1
        return {0: 0.24, 1: 0.5, 2: 0.76}.get(pos, 0.5)

    def refresh_visible_characters():
        active_name = renpy.store.current_speaker_name
        active_slot = renpy.store.current_speaker_slot
        has_active = any(
            data.get("visible")
            and (slot == active_slot or (data.get("name") and data.get("name") == active_name))
            for slot, data in renpy.store.current_chara_defs.items()
        )
        visible = []
        for slot, data in sorted(renpy.store.current_chara_defs.items()):
            if data.get("visible") and data.get("path"):
                is_active = slot == active_slot or data.get("name") == active_name
                visible.append(
                    {
                        "slot": slot,
                        "path": data.get("path"),
                        "xalign": slot_xalign(slot, data.get("position")),
                        "alpha": 1.0 if not has_active or is_active else 0.45,
                    }
                )
        renpy.store.current_characters = visible

    def set_active_speaker(speaker, slot=None):
        renpy.store.current_speaker_name = speaker
        renpy.store.current_speaker_slot = slot
        refresh_visible_characters()

    def apply_reader_node(node, api):
        node_type = node.get("type")
        if node_type == "scene":
            renpy.store.current_scene_id = node.get("scene_id")
            path = api.get_background_path(renpy.store.current_scene_id)
            renpy.store.current_background_path = path.replace("\\", "/") if path else None
            return True
        if node_type == "bgm":
            path = api.get_bgm_path(node.get("name"))
            if path:
                renpy.music.play(path, channel="music", loop=True, fadein=0.2)
            return True
        if node_type == "audio_stop":
            renpy.music.stop(channel="music", fadeout=0.2)
            return True
        if node_type == "chara_set":
            slot = node.get("slot")
            if slot:
                char_path = api.get_character_face_path(node.get("chara_id"), 0)
                renpy.store.current_chara_defs[slot] = {
                    "id": node.get("chara_id"),
                    "name": node.get("name"),
                    "position": node.get("position"),
                    "face": "0",
                    "path": char_path.replace("\\", "/") if char_path else None,
                    "visible": False,
                }
                refresh_visible_characters()
            return True
        if node_type == "chara_face":
            slot = node.get("slot")
            if slot and slot in renpy.store.current_chara_defs:
                renpy.store.current_chara_defs[slot]["face"] = node.get("face") or "0"
                char_path = api.get_character_face_path(
                    renpy.store.current_chara_defs[slot].get("id"),
                    renpy.store.current_chara_defs[slot].get("face"),
                )
                if char_path:
                    renpy.store.current_chara_defs[slot]["path"] = char_path.replace("\\", "/")
                refresh_visible_characters()
            return True
        if node_type == "chara_show":
            slot = node.get("slot")
            if slot and slot in renpy.store.current_chara_defs:
                if node.get("position") is not None:
                    renpy.store.current_chara_defs[slot]["position"] = node.get("position")
                renpy.store.current_chara_defs[slot]["visible"] = True
                refresh_visible_characters()
            return True
        if node_type == "chara_hide":
            slot = node.get("slot")
            if slot and slot in renpy.store.current_chara_defs:
                renpy.store.current_chara_defs[slot]["visible"] = False
                refresh_visible_characters()
            return True
        return False

    def save_current_marker():
        if renpy.store.current_reader_marker:
            persistent.reader_marker = dict(renpy.store.current_reader_marker)
            renpy.save_persistent()
            renpy.store.menu_notice = "Saved reading marker."

init 999 python:
    config.quit_action = Quit(confirm=False)
    style.default.font = "fonts/OpenSans-Regular.ttf"

screen loading_screen(message):
    tag loading
    frame:
        align (0.5, 0.5)
        xpadding 20
        ypadding 20
        xminimum 400
        yminimum 120
        has vbox
        
        text message size 28
        text "Please wait..." size 22
    
    add "running_fou":
            align(0.95,0.95)


screen message_screen(message):
    tag menu
    modal True
    frame:
        align (0.5, 0.5)
        xpadding 20
        ypadding 20
        xminimum 400
        yminimum 140
        has vbox

        text message size 26 substitute False
        textbutton "OK" action Return()

screen confirm(message, yes_action, no_action):
    modal True
    zorder 200

    frame:
        align (0.5, 0.5)
        xpadding 20
        ypadding 20
        xminimum 420
        has vbox

        text message size 26 substitute False
        hbox:
            spacing 16
            textbutton "Yes" action yes_action
            textbutton "No" action no_action

screen vn_stage(background_path, scene_id, characters):
    zorder 0

    if background_path:
        add background_path xysize (config.screen_width, config.screen_height)
    else:
        add Solid("#111318")

    for chara in characters:
        add chara["path"] xalign chara["xalign"] yalign 1.0 zoom 1.45 alpha chara["alpha"]

    if scene_id and not background_path:
        frame:
            align (0.02, 0.03)
            xpadding 10
            ypadding 6
            text "Scene [scene_id]" size 18

screen reader_dialogue(speaker, line):
    modal True
    zorder 80

    button:
        background None
        xfill True
        yfill True
        action Return(True)

    fixed:
        align (0.5, 1.0)
        xysize (760, 140)
        yoffset -2

        add "gui/fgo_textbox.png" xysize (760, 136) ypos 4

        if speaker and speaker != "Narrator":
            text speaker xpos 30 ypos 16 xmaximum 220 size 22 color "#ffffff" font "fonts/OpenSans-Regular.ttf" substitute False

        text line xpos 48 ypos 68 xmaximum 650 size 22 color "#ffffff" font "fonts/OpenSans-Regular.ttf" substitute False slow_cps 85 slow_abortable True

    key "dismiss" action Return(True)
    key "K_SPACE" action Return(True)
    key "K_RETURN" action Return(True)

screen reader_choice(choices):
    modal True
    zorder 85

    button:
        background None
        xfill True
        yfill True
        action NullAction()

    vbox:
        align (0.5, 0.58)
        spacing 10

        for i, choice in enumerate(choices):
            button:
                xysize (650, 54)
                background Frame("gui/fgo_textbox.png", 18, 18)
                hover_background Frame("gui/fgo_textbox.png", 18, 18)
                action Return(i)

                text choice xalign 0.5 yalign 0.5 xmaximum 610 size 22 color "#ffffff" font "fonts/OpenSans-Regular.ttf" substitute False

screen backlog_screen():
    modal True
    zorder 160

    frame:
        align (0.5, 0.5)
        xysize (720, 520)
        xpadding 20
        ypadding 18
        has vbox

        hbox:
            xfill True
            text "Backlog" size 34
            textbutton "Close" xalign 1.0 action Hide("backlog_screen")

        viewport mousewheel True draggable True:
            vbox:
                spacing 10
                for entry in backlog:
                    if entry.get("speaker"):
                        text entry.get("speaker") size 18 color "#9fc7ff" font "fonts/OpenSans-Regular.ttf" substitute False
                        text entry.get("line") size 20 font "fonts/OpenSans-Regular.ttf" substitute False

screen settings_screen():
    modal True
    zorder 170

    frame:
        align (0.5, 0.5)
        xysize (440, 240)
        xpadding 22
        ypadding 18
        has vbox

        text "Settings" size 34
        text "Music Volume" size 22
        bar value Preference("music volume") xmaximum 360
        text "Sound Volume" size 22
        bar value Preference("sound volume") xmaximum 360
        textbutton "Close" action Hide("settings_screen")

screen reader_nav():
    zorder 100

    hbox:
        align (0.98, 0.03)
        spacing 8

        textbutton "War List" action Jump("war_list_flow")
        textbutton "LOG" action Show("backlog_screen")
        textbutton "Save" action Function(save_current_marker)
        textbutton "Quit" action Quit(confirm=False)

    if menu_notice:
        frame:
            align (0.5, 0.04)
            xpadding 10
            ypadding 6
            text menu_notice size 18 substitute False

screen title_menu():
    tag menu
    
    add "gui/title_wallpaper.png" xysize (config.screen_width, config.screen_height)
    add "gui/title_text_fade.png" xysize (config.screen_width, config.screen_height)
    add "gui/logo_title.png":
        align (0.5, 0.35)
    hbox:
        align (0.5, 0.90)
        spacing 50

        textbutton "Start" action Jump("war_list_flow")
        if getattr(persistent, "reader_marker", None):
            textbutton "Continue" action [
                SetVariable("resume_marker", persistent.reader_marker),
                SetVariable("selected_war_id", persistent.reader_marker.get("war_id")),
                Jump("load_war"),
            ]

            textbutton "Load" action [
                SetVariable("resume_marker", persistent.reader_marker),
                SetVariable("selected_war_id", persistent.reader_marker.get("war_id")),
                Jump("load_war"),
            ]
        else:
            textbutton "Continue" action NullAction()
            textbutton "Load" action NullAction()
        textbutton "Settings" action Show("settings_screen")
        textbutton "Quit" action Quit(confirm=False)

    if menu_notice:
        frame:
            align (0.5, 0.94)
            xpadding 14
            ypadding 8
            text menu_notice substitute False

screen quest_title_card(quest):
    modal True
    zorder 90

    frame:
        align (0.5, 0.5)
        xmaximum 680
        xpadding 28
        ypadding 24
        has vbox

        $ war_title = quest.get("warLongName") or ""
        $ quest_name = quest.get("name") or "Unnamed Quest"
        $ spot_name = quest.get("spotName") or ""

        text war_title size 24 text_align 0.5 xalign 0.5 substitute False
        text quest_name size 34 text_align 0.5 xalign 0.5 substitute False
        if spot_name:
            text spot_name size 24 text_align 0.5 xalign 0.5 substitute False

        null height 16

        hbox:
            xalign 0.5
            spacing 12
            textbutton "Continue" action Return(True)
            textbutton "War List" action Jump("war_list_flow")
            textbutton "Quit" action Quit(confirm=False)

screen war_select():
    tag menu
    modal True
    frame:
        align (0.5, 0.5)
        xpadding 20
        ypadding 20
        xmaximum 900
        ymaximum 700
        has vbox

        text "Select a War" size 36

        if war_load_error:
            text war_load_error size 24 substitute False
            textbutton "Retry" action Return(False)
        else:
            viewport id "war_list_view" mousewheel True draggable True:
                vbox:
                    for war in war_list:
                        $ title = war.get("longName") or war.get("name") or "Unnamed War"
                        $ summary = "[war.get('id')] - [title]"
                        textbutton summary action [SetVariable("selected_war_id", war.get("id")), Return(True)]

        hbox:
            spacing 16
            textbutton "Refresh" action [SetVariable("war_list", []), SetVariable("war_load_error", None), Return(False)]
            textbutton "Quit" action Quit(confirm=False)

label start:
    $ menu_notice = ""
    call screen title_menu
    jump start

label war_list_flow:
    scene black
    with fade
    $ resume_marker = None

    if not war_list:
        show screen loading_screen("Fetching available NA Wars...")

        $ renpy.pause(0.1, hard=True)
        python:
            api = get_api()
            war_list_data = api.get_war_list()
        hide screen loading_screen

        if war_list_data is None:
            $ war_load_error = api.last_error or "Unable to fetch the war list. Check your internet connection."
            call screen message_screen(war_load_error)
            jump start

        python:
            war_list = sorted(war_list_data, key=lambda item: item.get("id", 0))
            war_list = [
                {
                    "id": item.get("id", 0),
                    "name": item.get("name", ""),
                    "longName": item.get("longName", ""),
                    "scriptId": item.get("scriptId", ""),
                    "script": item.get("script", ""),
                }
                for item in war_list
            ]
            war_load_error = None

    call screen war_select

    if not selected_war_id:
        jump start

    jump load_war

label load_war:
    show screen loading_screen("Loading war [selected_war_id]...")
    $ renpy.pause(0.1, hard=True)
    python:
        api = get_api()
        active_war = api.load_war(selected_war_id)
    hide screen loading_screen

    if active_war is None:
        $ war_load_error = api.last_error or "Failed to load the selected war. Please try another."
        call screen message_screen(war_load_error)
        jump start

    jump play_war

label play_war:
    scene black
    with fade
    $ current_background_path = None
    $ current_scene_id = None
    $ current_characters = []
    $ current_chara_defs = {}
    $ current_speaker_name = None
    $ current_speaker_slot = None
    $ backlog = []
    show screen vn_stage(current_background_path, current_scene_id, current_characters)
    show screen reader_nav

    $ war_name = active_war["war"].get("longName") or active_war["war"].get("name") or "Unknown War"
    n "Now playing: [war_name]"

    if active_war.get("story_quests"):
        $ quest_idx = resume_marker.get("quest_idx", 0) if resume_marker else 0
        $ resume_phase_idx = resume_marker.get("phase_idx", 0) if resume_marker else 0
        while quest_idx < len(active_war["story_quests"]):
            $ quest = active_war["story_quests"][quest_idx]
            call screen quest_title_card(quest)

            $ phase_idx = resume_phase_idx if resume_marker and quest_idx == resume_marker.get("quest_idx", 0) else 0
            while phase_idx < len(quest["phase_scripts"]):
                $ phase_script = quest["phase_scripts"][phase_idx]
                $ current_reader_marker = {"war_id": selected_war_id, "quest_idx": quest_idx, "phase_idx": phase_idx, "script_id": phase_script.get("scriptId"), "script": phase_script.get("script")}
                show screen loading_screen("Loading phase [phase_script.get('phase')]...")
                $ renpy.pause(0.1, hard=True)
                python:
                    phase_nodes = api.load_script_nodes(phase_script.get("script"))
                hide screen loading_screen

                if phase_nodes is None:
                    $ war_load_error = api.last_error or "Failed to load a phase script."
                    call screen message_screen(war_load_error)
                else:
                    $ idx = 0
                    while idx < len(phase_nodes):
                        $ node = phase_nodes[idx]
                        if node["type"] == "dialogue":
                            $ speaker = node.get("speaker") or "Narrator"
                            $ speaker_slot = node.get("speaker_slot")
                            $ text = node.get("text") or ""
                            if text:
                                $ set_active_speaker(speaker, speaker_slot)
                                $ record_dialogue(speaker, text)
                                call screen reader_dialogue(speaker, text)
                        elif node["type"] == "choice":
                            python:
                                choice_options, next_idx = collect_choice_options(phase_nodes, idx)
                            if choice_options:
                                call screen reader_choice(choice_options)
                            $ idx = next_idx - 1
                        elif apply_reader_node(node, api):
                            show screen vn_stage(current_background_path, current_scene_id, current_characters)
                        $ idx += 1

                $ phase_idx += 1
                $ resume_marker = None

            $ quest_idx += 1

        n "End of story."
        hide screen reader_nav
        hide screen vn_stage
        jump start

    if active_war["script_id"]:
        n "Script ID: [active_war['script_id']]"

    if not active_war["script_nodes"]:
        n "No parsed script content was found for this war."
        if active_war.get("script_url"):
            n "Atlas listed [active_war['script_url']], but it did not contain readable dialogue."
        n "Returning to the war list."
        hide screen reader_nav
        hide screen vn_stage
        jump start

    $ idx = 0
    while idx < len(active_war["script_nodes"]):
        $ node = active_war["script_nodes"][idx]
        if node["type"] == "dialogue":
            $ speaker = node.get("speaker") or "Narrator"
            $ speaker_slot = node.get("speaker_slot")
            $ text = node.get("text") or ""
            if text:
                $ set_active_speaker(speaker, speaker_slot)
                $ record_dialogue(speaker, text)
                call screen reader_dialogue(speaker, text)
        elif node["type"] == "choice":
            python:
                choice_options, next_idx = collect_choice_options(active_war["script_nodes"], idx)
            if choice_options:
                call screen reader_choice(choice_options)
            $ idx = next_idx - 1
        elif apply_reader_node(node, api):
            show screen vn_stage(current_background_path, current_scene_id, current_characters)
        $ idx += 1

    n "End of script."
    hide screen reader_nav
    hide screen vn_stage
    jump start
