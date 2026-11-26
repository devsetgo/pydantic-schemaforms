# About

`pydantic-schemaforms` is a Python library for generating **server-rendered HTML forms** from **Pydantic** models.

It focuses on:

- One Pydantic model for the form, its validation and its data
- HTML that is escaped by construction (text a user types can't inject code), built with Python 3.14 t-strings
- Sync and async rendering, tested with Flask and FastAPI. WSGI and ASGI are
  the two standard ways Python web apps talk to a server: Flask uses WSGI
  (sync), FastAPI uses ASGI (async)
- No external requests by default: assets are packaged and inlined, with explicit opt-in for CDNs

If you're new, start with the [Tutorial](tutorial/index.md). The
[Reference](reference/index.md) lists every input, layout and option.

Project links:

- Docs: https://devsetgo.github.io/pydantic-schemaforms/
- GitHub: https://github.com/devsetgo/pydantic-schemaforms
- PyPI: https://pypi.org/project/pydantic-schemaforms/


## About Me
I am a software engineering manager with an eclectic background in various industries (finance, manufacturing, and metrology). I am passionate about software development and love to learn new things.

- [DevSetGo.com](https://www.devsetgo.com)
- [Github](https://github.com/devsetgo)
- [X.com](https://x.com/MikeRyan353)
