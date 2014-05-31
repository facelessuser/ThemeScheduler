# ThemeScheduler

Sublime plugin to change your theme or apply filters to your themes at different times of the day. ST3 only.

# Optional Dependencies
- Applying filters requires ThemeTweaker plugin https://github.com/facelessuser/ThemeTweaker.

# Usage
Set your rules in `ThemeScheduler.sublime-settings` in your `User` folder (it will automatically be created).  Then set `"enabled": True`.

## Examples
Example for changing themes:
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

Example for using filters [(see ThemeTweaker filter documentation)](https://github.com/facelessuser/ThemeTweaker#custom-filter-command):
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
            "filters": "brightness(.97)@bg",
            "time": "11:00"
        }
    ]
```

Example for displaying messages at theme change:
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

Example for setting the UI theme. When changing a theme, Sublime may look funny because it does not refresh all of the UI.  You can try resizing the window, moving the element (like a tab) or restart Sublime.  ThemeScheduler has no control over this:
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

Example for running an ApplicationCommand (Application only!):
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

To use SubNotify plugin for notification messages, just enable SubNotify usage (assuming SubNotify has been installed):

```javascript
{
    "enabled": true,
    "use_sub_notify": true,
    "themes":
    [
        {
```

# License

Theme Scheduler is released under the MIT license.

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
