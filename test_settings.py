#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals


HELPER_SETTINGS = {}


def run():
    from djangocms_helper import runner
    runner.cms('djangocms_link_manager')


if __name__ == "__main__":
    run()
