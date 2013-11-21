"""
Theme Scheduler

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
License: MIT

Example Theme file (ThemeScheduler.sublime-settings):
{
    "enabled": true,
    "themes":
    [
        {
            "theme": "Packages/User/Color Scheme/sometheme.tmTheme",
            "time": "21:30"
        },
        {
            "theme": "Packages/User/Color Scheme/someothertheme.tmTheme",
            "time": "8:30"
        }
    ]
}

Uses multiconf for "enabled" and "themes" key for platform or host specific settings.
See multiconf.py for more details.

Creates theme file if it doesn't exists (turned off by default).
"""

from datetime import datetime, timedelta
import time
import sublime
import sublime_plugin
from collections import namedtuple
import _thread as thread
from .lib.file_strip.json import sanitize_json
from .lib.multiconf import get as multiget
import json
from os.path import exists, join, abspath, dirname
LOAD_RETRIES = 5


def log(s):
    print("ThemeScheduler: %s" % s)


def debug_log(s):
    if SETTINGS.get("debug", False):
        log(s)


def create_settings(settings_path):
    err = False
    default_theme = {
        "enabled": False,
        "themes": [],
    }
    j = json.dumps(default_theme, sort_keys=True, indent=4, separators=(',', ': '))
    try:
        with open(settings_path, 'w') as f:
            f.write(j + "\n")
    except:
        err = True
    return err


def total_seconds(t):
    return (t.microseconds + (t.seconds + t.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def get_current_time():
    now = datetime.now()
    seconds = total_seconds(timedelta(hours=now.hour, minutes=now.minute, seconds=now.second))
    return seconds, now


def translate_time(t):
    tm = time.strptime(t, '%H:%M')
    return total_seconds(timedelta(hours=tm.tm_hour, minutes=tm.tm_min, seconds=tm.tm_sec))


def blocking_message(msg):
    sublime.ok_cancel_dialog(msg)
    ThemeScheduler.update = True


class ThemeSchedulerGetNextChangeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        sublime.message_dialog("ThemeScheduler: Next Change @\n" + str(ThemeScheduler.next_change))


class ThemeSchedulerRefreshCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        manage_thread()


class ThemeRecord(namedtuple('ThemeRecord', ["time", "theme", "msg", "filters"])):
    pass


class ThreadMgr(object):
    restart = False
    kill = False


class ThemeScheduler(object):
    themes = []
    current_theme = ""
    current_msg = None
    current_filters = None
    next_change = None
    day = None
    ready = False
    busy = False
    update = False
    current_time = None
    set_safe = False

    @classmethod
    def init(cls, set_safe=False):
        """
        Initialize theme changer object
        """
        cls.ready = False
        cls.set_safe = set_safe

        cls.themes = []
        for t in multiget(SETTINGS, "themes", []):
            theme_time = translate_time(t["time"])
            theme = t["theme"]
            msg = t.get("msg", None)
            filters = t.get("filters", None)
            cls.themes.append(ThemeRecord(theme_time, theme, msg, filters))
        seconds, now = get_current_time()
        cls.get_next_change(seconds, now, startup=True)
        cls.ready = True

    @classmethod
    def set_startup_theme(cls):
        """
        Set startup theme
        """

        if cls.next_change is not None:
            closest = None
            greatest = None
            seconds = get_current_time()[0]
            for t in cls.themes:
                if t.time < seconds and (closest is None or t.time > closest.time):
                    closest = t
                elif greatest is None or t.time > greatest.time:
                    greatest = t
            if closest is None:
                closest = cls.next_change if greatest is None else greatest

            if closest is not None:
                if cls.current_time is not None and closest.time == cls.current_time:
                    cls.update_theme(closest.theme, None, closest.filters)
                else:
                    cls.current_time = closest.time
                    cls.update_theme(closest.theme, closest.msg, closest.filters)

    @classmethod
    def get_next_change(cls, seconds, now, startup=False):
        """
        Get the next time point in which the theme should change.  Store the theme record.
        """

        # Reset tracker members
        cls.next_change = None
        cls.day = None

        # Try and find the closest time point to switch the theme
        closest = None
        lowest = None
        for t in cls.themes:
            if seconds <= t.time and (closest is None or t.time < closest.time):
                closest = t
            elif lowest is None or t.time < lowest.time:
                lowest = t

        # Select the closest if there was one
        if closest is not None:
            cls.next_change = closest
        elif lowest is not None:
            cls.next_change = lowest
            cls.day = now.day

        debug_log("%s - Next Change @ %s" % (time.ctime(), str(cls.next_change)))

        if startup:
            cls.set_startup_theme()

    @classmethod
    def change_theme(cls):
        """
        Change the theme and get the next time point to change themes.
        """

        # Change the theme
        if (
            cls.next_change is not None and
            (
                cls.next_change.theme != cls.current_theme or
                cls.next_change.msg != cls.current_msg or
                cls.next_change.filters != cls.current_filters
            )
        ):
            debug_log("Making Change!")
            debug_log("Desired Next: %s Current: %s" % (str(cls.next_change), str(cls.current_theme)))
            theme, msg, filters = cls.next_change.theme, cls.next_change.msg, cls.next_change.filters
            cls.current_theme = theme
            cls.current_msg = msg
            cls.current_filters = filters
            # Get the next before changing
            if cls.current_time is not None and cls.next_change.time == cls.current_time:
                cls.update_theme(theme, None, filters)
            else:
                cls.current_time = cls.next_change.time
                cls.update_theme(theme, msg, filters)
        else:
            debug_log("Change not made!")
            debug_log("Desired Next: %s Current: %s" % (str(cls.next_change), str(cls.current_theme)))
        seconds, now = get_current_time()
        cls.get_next_change(seconds, now)

    @classmethod
    def tweak_theme(cls, theme, msg, filters):
        relase_busy = True
        debug_log("Using Theme Tweaker to adjust file!")
        sublime.run_command("theme_tweaker_custom", {"theme": theme, "filters": filters})
        if msg is not None and isinstance(msg, str):
            relase_busy = False
            sublime.set_timeout(lambda: blocking_message(msg), 3000)
        return relase_busy

    @classmethod
    def swap_theme(cls, theme, msg):
        relase_busy = True
        debug_log("Selecting installed theme!")
        if cls.set_safe:
            if exists(pref_file):
                try:
                    with open(pref_file, "r") as f:
                        # Allow C style comments and be forgiving of trailing commas
                        content = sanitize_json(f.read(), True)
                    pref = json.loads(content)
                except:
                    pass
            pref['color_scheme'] = theme
            j = json.dumps(pref, sort_keys=True, indent=4, separators=(',', ': '))
            try:
                with open(pref_file, 'w') as f:
                    f.write(j + "\n")
                if msg is not None and isinstance(msg, str):
                    relase_busy = False
                    sublime.set_timeout(lambda: blocking_message(msg), 3000)
            except:
                pass
        else:
            sublime.load_settings("Preferences.sublime-settings").set("color_scheme", theme)
            if msg is not None and isinstance(msg, str):
                relase_busy = False
                sublime.set_timeout(lambda: blocking_message(msg), 3000)
        return relase_busy

    @classmethod
    def update_theme(cls, theme, msg, filters):
        # When sublime is loading, the User preference file isn't available yet.
        # Sublime provides no real way to tell when things are intialized.
        # Handling the preference file ourselves allows us to avoid obliterating the User preference file.
        debug_log("Theme: %s" % str(theme))
        debug_log("Msg: %s" % str(msg))
        debug_log("Filters: %s" % str(filters))
        if cls.busy:
            return
        cls.busy = True
        relase_busy = True
        pref_file = join(sublime.packages_path(), 'User', 'Preferences.sublime-settings')
        pref = {}
        if filters is not None:
            if is_tweakable():
                cls.tweak_theme(theme, msg, filters)
            else:
                debug_log("ThemeTweaker is not installed :(")
                cls.swap_theme(theme, msg)
        else:
            cls.swap_theme(theme, msg)

        if relase_busy:
            cls.busy = False


def theme_loop():
    """
    Loop for checking when to change the theme.
    """

    def is_update_time(seconds, now):
        update = False
        if not ThemeScheduler.busy and ThemeScheduler.next_change is not None and not ThemeScheduler.update:
            update = (
                (ThemeScheduler.day is None and seconds >= ThemeScheduler.next_change.time) or
                (ThemeScheduler.day != now.day and seconds >= ThemeScheduler.next_change.time)
            )
        return update

    sublime.set_timeout(ThemeScheduler.init, 0)

    while not ThreadMgr.restart and not ThreadMgr.kill:
        # Pop back into the main thread and check if time to change theme
        seconds, now = get_current_time()
        if ThemeScheduler.update:
            ThemeScheduler.update = False
            ThemeScheduler.busy = False
            debug_log("Button defferal")
            debug_log("is busy: %s" % str(ThemeScheduler.busy))
            debug_log(
                "Compare: day: %s now: %s next: %s seconds: %s" % (
                    str(ThemeScheduler.day) if ThemeScheduler.day is not None else "None",
                    str(now.day),
                    str(ThemeScheduler.next_change.time) if ThemeScheduler.next_change is not None else "None",
                    str(seconds)
                )
            )
            sublime.set_timeout(lambda: ThemeScheduler.get_next_change(seconds, now, startup=True), 0)
        elif ThemeScheduler.ready and is_update_time(seconds, now):
            debug_log("Time to update")
            debug_log("is busy: %s" % str(ThemeScheduler.busy))
            debug_log(
                "Compare: day: %s now: %s next: %s seconds: %s" % (
                    str(ThemeScheduler.day) if ThemeScheduler.day is not None else "None",
                    str(now.day),
                    str(ThemeScheduler.next_change.time) if ThemeScheduler.next_change is not None else "None",
                    str(seconds)
                )
            )
            sublime.set_timeout(lambda: ThemeScheduler.change_theme(), 0)
        time.sleep(1)

    if ThreadMgr.restart:
        ThreadMgr.restart = False
        sublime.set_timeout(manage_thread, 0)
    if ThreadMgr.kill:
        ThreadMgr.kill = False


def manage_thread(first_time=False, restart=False):
    """
    Manage killing, starting, and restarting the thread
    """

    global running_theme_scheduler_loop
    if not multiget(SETTINGS, 'enabled', 'False'):
        running_theme_scheduler_loop = False
        ThreadMgr.kill
        log("Kill Thread")
    elif not restart and (first_time or not running_theme_scheduler_loop):
        running_theme_scheduler_loop = True
        thread.start_new_thread(theme_loop, ())
        log("Start Thread")
    else:
        running_theme_scheduler_loop = False
        ThreadMgr.restart = True
        log("Restart Thread")


def is_tweakable():
    tweakable = False
    for app_command in sublime_plugin.application_command_classes:
        if app_command.__name__ == "ThemeTweakerIsReadyCommand":
            tweakable = app_command.is_tweakable()
            break
    return tweakable


def tweak_loaded():
    tweak_ready_command = None
    ready = False
    for app_command in sublime_plugin.application_command_classes:
        if app_command.__name__ == "ThemeTweakerIsReadyCommand":
            tweak_ready_command = app_command
            break
    if tweak_ready_command is not None:
        ready = tweak_ready_command.is_tweakable()
    else:
        ready = True
    return ready


def load_plugin(retries):
    global SETTINGS

    if tweak_loaded() or retries == 0:
        log("ThemeScheduler: Loading...")
        settings_file = "ThemeScheduler.sublime-settings"
        settings_path = join(sublime.packages_path(), 'User', settings_file)
        if not exists(settings_path):
            create_settings(settings_path)

        # Init the settings object
        SETTINGS = sublime.load_settings(settings_file)
        SETTINGS.clear_on_change('reload')
        SETTINGS.add_on_change('reload', manage_thread)

        first_time = not 'running_theme_scheduler_loop' in globals()
        global running_theme_scheduler_loop
        running_theme_scheduler_loop = not first_time
        manage_thread(first_time, not first_time)
    else:
        retries_left = retries - 1
        log("ThemeScheduler: Waiting for ThemeTweaker...")
        sublime.set_timeout(lambda: load_plugin(retries_left), 300)


def plugin_loaded():
    load_plugin(LOAD_RETRIES)
