"""
Theme Scheduler

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
License: MIT

Example Theme file (ThemeScheduler.sublime-settings):
{
    "enabled": true,
    "use_sub_notify": false,
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
from os.path import exists, join

LOAD_RETRIES = 5
SETTINGS = {}


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


def datetime2sec(t):
    tm = time.strptime(t, '%H:%M')
    return total_seconds(timedelta(hours=tm.tm_hour, minutes=tm.tm_min, seconds=tm.tm_sec))


def sec2time(total):
    seconds = total % 60
    t_minutes = (total / 60)
    minutes = t_minutes % 60
    hours = t_minutes / 60
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def display_message(msg):
    settings = sublime.load_settings("ThemeScheduler.sublime-settings")
    use_sub_notify = multiget(settings, "use_sub_notify", False)
    if use_sub_notify:
        sublime.run_command("sub_notify", {"title": "ThemeScheduler", "msg": msg})
    else:
        if ThemeScheduler.dialog_open:
            log("Dialog already open!")
            log(msg)
            return
        ThemeScheduler.dialog_open = True
        sublime.ok_cancel_dialog(msg)
        ThemeScheduler.update = True
        ThemeScheduler.dialog_open = False


class ThemeSchedulerGetNextChangeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        sublime.message_dialog("ThemeScheduler: Next Change @\n" + str(ThemeScheduler.next_change))


class ThemeSchedulerRefreshCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        manage_thread()


class ThemeRecord(namedtuple('ThemeRecord', ["time", "theme", "msg", "filters", "ui_theme", "command"])):
    def __str__(self):
        return 'ThemeRecord(\n    time=%s,\n    theme=%s,\n    msg=%s,\n    filters=%s,\n    ui_theme=%s,\n    command=%s\n)' % (
            sec2time(self.time), self.theme, self.msg,
            self.filters, self.ui_theme, self.command
        )

    __repr__ = __str__


class CommandWrapper(object):
    def __init__(self, cmd):
        self.cmd = cmd["command"]
        self.args = cmd.get("args", {})

    def __str__(self):
        return self.cmd

    __repr__ = __str__

    def run(self):
        sublime.run_command(self.cmd, self.args)


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
    dialog_open = False
    current_ui_theme = None
    current_command = None

    @classmethod
    def reset_msg_state(cls):
        """
        Reset the current state of dialogs
        """
        cls.dialog_open = False

    @classmethod
    def init(cls, set_safe=False):
        """
        Initialize theme changer object
        """

        cls.busy = True
        cls.ready = False
        cls.set_safe = set_safe

        cls.themes = []
        for t in multiget(SETTINGS, "themes", []):
            theme_time = datetime2sec(t["time"])
            theme = t.get("theme", None)
            msg = t.get("msg", None)
            filters = t.get("filters", None)
            ui_theme = t.get("ui_theme", None)
            command = t.get("command", None)
            if command is not None:
                command = CommandWrapper(command)
            cls.themes.append(ThemeRecord(theme_time, theme, msg, filters, ui_theme, command))
        seconds, now = get_current_time()
        cls.update_theme(seconds, now)
        cls.ready = True
        cls.busy = False

    @classmethod
    def update_next(cls, seconds, now):
        # Reset tracker members
        cls.next_change = None
        cls.day = None

        # Try and find the closest time point to switch the theme
        closest = None
        lowest = None
        for t in cls.themes:
            if seconds < t.time and (closest is None or t.time < closest.time):
                closest = t
            if lowest is None or t.time < lowest.time:
                lowest = t

        # Select the closest if there was one
        if closest is not None:
            cls.next_change = closest
        elif lowest is not None:
            cls.next_change = lowest
        if lowest is not None:
            cls.lowest = lowest

        if (cls.next_change.time == cls.lowest.time and seconds < cls.lowest.time):
            # The next change is the first of the next day
            # But the time is not greater meaning we are already
            # the next day, intialize to -1 to signify the last good
            # change was yesterday.
            cls.day = -1
        else:
            # Copy the day in which the next change was picked
            cls.day = now.day

        debug_log("Today = %d" % cls.day)
        debug_log("%s - Next Change @ %s" % (time.ctime(), str(cls.next_change)))

    @classmethod
    def update_current(cls):
        """
        Set next theme
        """

        if cls.next_change is not None:
            closest = None
            greatest = None
            seconds = get_current_time()[0]
            for t in cls.themes:
                if t.time <= seconds and (closest is None or t.time > closest.time):
                    closest = t
                elif greatest is None or t.time > greatest.time:
                    greatest = t
            if closest is None:
                closest = cls.next_change if greatest is None else greatest

            if closest is not None:
                cls.apply_changes(
                    closest.theme,
                    closest.msg,
                    closest.filters,
                    closest.ui_theme,
                    closest.command
                )

    @classmethod
    def update_theme(cls, seconds, now, update=True):
        """
        Get the next time point in which the theme should change.  Store the theme record.
        Update current theme if required.
        """

        cls.update_next(seconds, now)

        if update:
            cls.update_current()

    @classmethod
    def on_post_dialog(cls, seconds, now):
        """
        Precation to make sure an update isn't needed
        that was prevented because of message dialog.
        Maybe this can be removed in the future.
        """

        cls.busy = True
        update = True
        last_next = cls.next_change
        cls.update_next(seconds, now)

        if last_next is None:
            if cls.next_change is None:
                debug_log("After dialog - No update needed.")
                update = False
        elif cls.next_change is not None and cls.next_change.time == last_next.time:
            debug_log("After dialog - No update needed.")
            update = False

        if update:
            debug_log("After dialog - Update needed.")
            cls.update_current()
        cls.busy = False

    @classmethod
    def on_change(cls, seconds, now):
        """
        Change the theme and get the next time point to change themes.
        """

        cls.busy = True
        # Change the theme
        if (
            cls.next_change is not None and
            (
                cls.next_change.theme != cls.current_theme or
                cls.next_change.msg != cls.current_msg or
                cls.next_change.filters != cls.current_filters or
                cls.next_change.ui_theme != cls.current_ui_theme or
                cls.next_change.command is not None
            )
        ):
            debug_log("Change needed!")
            update = True
        else:
            debug_log("Change not needed!")
            update = False

        cls.update_theme(seconds, now, update)
        cls.busy = False

    @classmethod
    def set_theme(cls, theme, ui_theme):
        """
        Apply the theme(s)
        """

        if cls.set_safe:
            # When sublime is loading, the User preference file isn't available yet.
            # Sublime provides no real way to tell when things are intialized.
            # Handling the preference file ourselves allows us to avoid
            # obliterating the User preference file.
            pref_file = join(sublime.packages_path(), 'User', 'Preferences.sublime-settings')
            pref = {}
            if exists(pref_file):
                try:
                    with open(pref_file, "r") as f:
                        # Allow C style comments and be forgiving of trailing commas
                        content = sanitize_json(f.read(), True)
                    pref = json.loads(content)
                except:
                    log("Failed to open preference file!")
                    return
            if ui_theme is not None:
                debug_log("Selecting UI theme!")
                pref['theme'] = ui_theme
            if theme is not None:
                debug_log("Selecting theme!")
                pref['color_scheme'] = theme
            j = json.dumps(pref, sort_keys=True, indent=4, separators=(',', ': '))
            try:
                with open(pref_file, 'w') as f:
                    f.write(j + "\n")
            except:
                log("Failed to write preference file!")
        else:
            if ui_theme is not None:
                debug_log("Selecting UI theme!")
                sublime.load_settings("Preferences.sublime-settings").set("theme", ui_theme)
            if theme is not None:
                debug_log("Selecting theme!")
                sublime.load_settings("Preferences.sublime-settings").set("color_scheme", theme)

    @classmethod
    def apply_changes(cls, theme, msg, filters, ui_theme, command):
        """
        Update theme.  Set the theme, then get the next one in line.
        """

        debug_log(
            "apply_changes(\n    theme=%s\n    msg=%s,\n    filters=%s,\n    ui_theme=%s,\n    command=%s\n)" % (
                theme, msg, filters, ui_theme, command
            )
        )

        if cls.next_change is not None:
            cls.current_time = cls.next_change.time
        cls.current_theme = theme
        cls.current_ui_theme = ui_theme
        cls.current_msg = msg
        cls.current_filters = filters
        if filters is not None:
            if is_tweakable():
                debug_log("Using Theme Tweaker to adjust file!")
                sublime.run_command(
                    "theme_tweaker_custom",
                    {"theme": theme, "filters": filters}
                )
                if ui_theme is not None:
                    cls.set_theme(None, ui_theme)
            else:
                debug_log("ThemeTweaker is not installed :(")
                cls.set_theme(theme, ui_theme)
        else:
            cls.set_theme(theme, ui_theme)

        try:
            if command is not None:
                command.run()
        except Exception as e:
            log("Command %s failed!" % str(command))
            log("\n%s" % str(e))

        if msg is not None and isinstance(msg, str):
            sublime.set_timeout(lambda m=msg: display_message(m), 3000)


def theme_loop():
    """
    Loop for checking when to change the theme.
    """

    def is_update_time(seconds, now):
        update = False
        if (
            not ThemeScheduler.busy and
            ThemeScheduler.next_change is not None and
            not ThemeScheduler.update and
            ThemeScheduler.day is not None
        ):
            if ThemeScheduler.day == now.day:
                # Comparing time on the same day
                # If the next change also equals the lowest,
                # it is the first change of the day.
                # Wait for the next day.
                update = (
                    seconds >= ThemeScheduler.next_change.time and
                    ThemeScheduler.next_change.time != ThemeScheduler.lowest.time
                )
            else:
                # Its a new day.  If the time is greater than the next or
                # even the lowest, update theme.
                update = (
                    seconds >= ThemeScheduler.next_change.time or
                    seconds >= ThemeScheduler.lowest.time
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
            debug_log("Is busy: %s" % str(ThemeScheduler.busy))
            debug_log(
                "Compare: day: %s now: %s next: %s current: %s" % (
                    ThemeScheduler.day if ThemeScheduler.day is not None else "None",
                    now.day,
                    sec2time(ThemeScheduler.next_change.time) if ThemeScheduler.next_change is not None else "None",
                    sec2time(seconds)
                )
            )
            sublime.set_timeout(lambda s=seconds, n=now: ThemeScheduler.on_post_dialog(s, n), 0)
        elif ThemeScheduler.ready and is_update_time(seconds, now):
            debug_log("Time to update")
            debug_log("Is busy: %s" % str(ThemeScheduler.busy))
            debug_log(
                "Compare: day: %s now: %s next: %s current: %s" % (
                    ThemeScheduler.day if ThemeScheduler.day is not None else "None",
                    now.day,
                    sec2time(ThemeScheduler.next_change.time) if ThemeScheduler.next_change is not None else "None",
                    sec2time(seconds)
                )
            )
            sublime.set_timeout(lambda s=seconds, n=now: ThemeScheduler.on_change(s, n), 0)
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
            tweakable = app_command.is_ready()
            break
    return tweakable


def external_plugins_loaded(plugins):
    for p in plugins:
        command = None
        ready = False
        for app_command in sublime_plugin.application_command_classes:
            if app_command.__name__ == p:
                command = app_command
                break
        if command is not None:
            ready = command.is_ready()
        else:
            # Command isn't found in list, so just return ready
            ready = True
    return ready


def load_plugin(retries):
    global SETTINGS
    ThemeScheduler.reset_msg_state()
    external_plugins = ["SubNotifyIsReadyCommand", "ThemeTweakerIsReadyCommand"]
    if external_plugins_loaded(external_plugins) or retries == 0:
        log("ThemeScheduler: Loading...")
        settings_file = "ThemeScheduler.sublime-settings"
        settings_path = join(sublime.packages_path(), 'User', settings_file)
        if not exists(settings_path):
            create_settings(settings_path)

        # Init the settings object
        SETTINGS = sublime.load_settings(settings_file)
        SETTINGS.clear_on_change('reload')
        SETTINGS.add_on_change('reload', manage_thread)

        first_time = 'running_theme_scheduler_loop' not in globals()
        global running_theme_scheduler_loop
        running_theme_scheduler_loop = not first_time
        manage_thread(first_time, not first_time)
    else:
        retries_left = retries - 1
        log("ThemeScheduler: Waiting for ThemeTweaker...")
        sublime.set_timeout(lambda: load_plugin(retries_left), 300)


def plugin_loaded():
    load_plugin(LOAD_RETRIES)


def plugin_unloaded():
    ThreadMgr.kill = True
