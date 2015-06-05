# User Guide {: .doctitle}
Configuration and usage of ThemeScheduler.

---

## General Use
Set your rules in `ThemeScheduler.sublime-settings` in your `User` folder (it will automatically be created).  Then set `"enabled": True`.

### Optional Dependencies
- Applying filters requires [ThemeTweaker plugin](https://github.com/facelessuser/ThemeTweaker).
- Alternative notifications require the [SubNotify plugin](https://github.com/facelessuser/SubNotify).

## Examples
### Changing Themes

```javascript
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

### Using filters
See ThemeTweaker's [custom filter documentationn](http://facelessuser.github.io/ThemeTweaker/usage/#custom-filter) for more info on configuring filter options.  The `filters` argument is constructed the same way.

```javascript
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
Messages will be done through the Sublime API via a popup dialog.  If you using the [SubNotify plugin](https://github.com/facelessuser/SubNotify) with the `use_subnotify` option enabled, messages will be displayed through SubNotify.

```javascript
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
When changing a theme, Sublime may look funny because it does not refresh all of the UI.  You can try resizing the window, moving the element (like a tab) or restart Sublime.  ThemeScheduler has no control over this, so if the results are unsatisfactory, then simply don't use it.

```javascript
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

### Run a Sublime ApplicationCommand
Cuttently ThemeScheduler only allows `Application` commands to be run on change.  Command support allows setting the specific commands and the arguments for the command.

```javascript
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
Theme Scheduler has only a small handful of settings.

### enabled
This is a boolean that controls whether ThemeScheduler is active.

```js
"enabled": true
```

### use_sub_notify
To use [SubNotify plugin](https://github.com/facelessuser/SubNotify) for notification messages, just enable SubNotify usage (assuming SubNotify has been installed) with this setting.

```js
"use_sub_notify": true,
```

### themes
This is an array of all your theme scheduler rules.

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
