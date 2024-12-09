#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
"""
Start the application and give control to curryrtool.application().

Bootstrap. It is responsible for initializing the application and transfer control to
curryrtool.application (); for this, it accepts the necessary console parameters
and configure the program properly.
"""


if __name__ == "__main__":
    from curryrtoolslib.loader.main import startup

    startup()
