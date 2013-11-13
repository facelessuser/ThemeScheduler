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
