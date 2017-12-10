# wunderlog

log weather-underground forecasts and observations.

I'm curious about trends in the Weather Underground forecast.
It seems to have a systematic bias late in the 10 day forecast,
and collecting forecast history is the first step in investigating that.

API token is retrieved from netrc, e.g. in `~/.netrc`:

```
machine api.wunderground.com
  password YOUR_TOKEN
  login YOUR_EMAIL
```

Uses recent Python features (pathlib, f-strings),
so requires Python ≥ 3.6.

Once I have some data collected, I'll update this to load things into a database and do some analytics.
