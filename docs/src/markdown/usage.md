# User Guide

Configuration and usage of ThemeScheduler.

## General Use

Set your rules in `User/ThemeScheduler.sublime-settings` (it will automatically be created).  Then set
`#!js "enabled": True`.

### Optional Dependencies

-   Applying filters requires [ThemeTweaker plugin](https://github.com/facelessuser/ThemeTweaker).
-   Alternative notifications require the [SubNotify plugin](https://github.com/facelessuser/SubNotify).

## Examples

### Changing Themes

```js
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
```

[Package Control](https://packagecontrol.io/) will usually install theme packages as zip files with the
`.sublime-package` extension in `Installed Packages` instead of the `Packages` folder, but you treat them as if they are
stored in the `Packages` folder unzipped. Sublime handles the abstraction. For example, we will assume a package tmTheme
file is installed in the root of a zipped package at `Installed Packages/Github Color Theme.subime-pakcage`:

```js
    "themes":
    [
        {
            "theme": "Packages/One Dark Color Scheme/One Dark.tmTheme",
            "time": "21:30"
        },
        {
            "theme": "Packages/Github Color Theme/GitHub.tmTheme",
            "time": "8:30"
        }
    ]
```

If a tmTheme is is installed in a sub-folder(s) within the zip, you would specify those the sub-folder(s) as well:

```js
    "themes":
    [
        {
            "theme": "Packages/Github Color Theme/sub-folder/GitHub.tmTheme",
            "time": "8:30"
        }
    ]
```

### Using filters

See ThemeTweaker's [custom filter documentation](http://facelessuser.github.io/ThemeTweaker/usage/#custom-filter) for
more info on configuring filter options.  The `filters` argument is constructed the same way.

```js
    "themes":
    [
        {
            "theme": "Packages/User/Color Scheme/Tomorrow-Night-Eighties.tmTheme",
            "filters": "brightness(.98)@bg",
            "time": "10:00"
        },
        {
            "theme": "Packages/User/Color Scheme/Tomorrow-Night-Eighties.tmTheme",
            "filters": "brightness(.97)@bg;glow(.1)",
            "time": "11:00"
        }
    ]
```

### Displaying Messages at Theme Change

Messages will be done through the Sublime API via a popup dialog or status bar.  If you are using the
[SubNotify plugin](https://github.com/facelessuser/SubNotify) with the `use_sub_notify` option enabled in the settings
file, messages will be displayed through SubNotify.

```js
    "themes":
    [
        {
            // Lunch
            "theme": "Packages/User/Color Scheme/Tomorrow-Night-Eighties.tmTheme",
            "filters": "brightness(.96)@bg;glow(.1)",
            "time": "12:00",
            "msg": "Lunch time!"
        }
    ]
```

### Setting the UI Theme

When changing a theme, Sublime may look funny because it does not refresh all of the UI.  You can try resizing the
window, moving the element (like a tab) or restart Sublime.  ThemeScheduler has no control over this, so if the results
are unsatisfactory, or you find yourself restarting Sublime to clear the glitches, then this feature may not be one that
you want to use.  If in the future, Sublime handles theme refresh better on theme changes, this feature may become even
more useful.

```js
{
    // Lunch
    "theme": "Packages/User/Color Scheme/Tomorrow-Night-Eighties.tmTheme",
    "filters": "brightness(.96)@bg;glow(.1)",
    "time": "12:00",
    "msg": "Lunch time!",
    "ui_theme": "Aprosopo Dark@st3.sublime-theme",
    "time": "21:00"
},
```

### Run a Sublime `ApplicationCommand`

ThemeScheduler allows setting a specific command with arguments.  ThemeScheduler currently, only allows `Application`
commands to be run on change.  You can work around this by simply writing an application command that wraps around view
or windows commands if you absolutely have to run them.

```js
{
    // Lunch
    "theme": "Packages/User/Color Scheme/Tomorrow-Night-Eighties.tmTheme",
    "filters": "brightness(.96)@bg;glow(.1)",
    "time": "12:00",
    "msg": "Lunch time!",
    "command": {
        "command": "set_aprosopo_theme", "args":
        {
            "theme": "light",
            "color": "blue"
        }
    },
    "time": "21:00"
},
```

## Settings

Theme Scheduler has only a small handful of settings outside the theme change rules.

### `enabled`

This is a boolean that controls whether ThemeScheduler is active.

```js
"enabled": true
```

### `use_sub_notify`

To use [SubNotify plugin](https://github.com/facelessuser/SubNotify) for notification messages, just enable SubNotify
usage with this setting (assuming SubNotify has been installed).

```js
"use_sub_notify": true,
```

### `themes`

This is an array of all your ThemeScheduler rules.

```js

"themes": [
    {
        // Lunch
        "theme": "Packages/User/Color Scheme/Tomorrow-Night-Eighties.tmTheme",
        "filters": "brightness(.96)@bg;glow(.1)",
        "time": "12:00",
        "msg": "Lunch time!",
        "ui_theme": "Aprosopo Dark@st3.sublime-theme",
        "time": "21:00"
    }
]
```
