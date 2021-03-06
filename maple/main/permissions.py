#!/usr/bin/env python
# -*- coding=UTF-8 -*-
# *************************************************************************
#   Copyright © 2015 JiangLin. All rights reserved.
#   File Name: permissions.py
#   Author:JiangLin
#   Mail:xiyang0807@gmail.com
#   Created Time: 2015-12-12 20:28:00
# *************************************************************************
from maple import app, db
from flask_login import current_user
from flask_principal import Permission, RoleNeed, UserNeed, identity_loaded
from functools import wraps
from flask import g, redirect, flash, url_for, abort, jsonify
from datetime import datetime, timedelta


class MyPermission(object):
    def __init__(self, required=None, name=None):
        self.required = required

    def __call__(self, func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if not self.allow():
                return self.action()
            return func(*args, **kwargs)

        return decorator

    def allow(self):
        return False

    def action(self):
        abort(403)


class OwnPermission(MyPermission):
    def allow(self):
        if current_user.username == g.user_url:
            return True
        else:
            return False

    def action(self):
        return redirect(url_for('index.index'))


class GuestPermission(MyPermission):
    def allow(self):
        if not g.user.is_authenticated:
            return True
        else:
            return False

    def action(self):
        flash('你已经登陆,不能重复登陆')
        return redirect(url_for('index.index'))


class TimePermission(MyPermission):
    def allow(self):
        if not current_user.send_email_time:
            current_user.send_email_time = datetime.now()
            db.session.commit()
        if datetime.now() < current_user.send_email_time + \
                timedelta(seconds=360):
            return True
        else:
            return False

    def action(self):
        return jsonify(judge=False, error="你获取的验证链接还未过期，请尽快验证")


own_permission = OwnPermission()
guest_permission = GuestPermission()
time_permission = TimePermission()

super_permission = Permission(RoleNeed('super'))
admin_permission = Permission(RoleNeed('admin')).union(super_permission)
writer_permission = Permission(RoleNeed('writer')).union(admin_permission)
visitor_permission = Permission(RoleNeed('visitor')).union(writer_permission)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'roles'):
        identity.provides.add(RoleNeed(current_user.roles))

    if hasattr(current_user, 'is_superuser'):
        if current_user.is_superuser:
            identity.provides.add(RoleNeed('super'))

    if hasattr(current_user, 'is_confirmed'):
        if current_user.is_confirmed:
            identity.provides.add(RoleNeed('writer'))

    if hasattr(current_user, 'is_authenticated'):
        if not current_user.is_authenticated:
            identity.provides.add(RoleNeed('guest'))
