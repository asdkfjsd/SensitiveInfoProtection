from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ext import db
from models import User, Role

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def require_admin():
    return current_user.is_authenticated and current_user.has_role("admin")

@admin_bp.before_request
def guard():
    if not require_admin():
        from flask import abort
        abort(403)

@admin_bp.get("/users")
def users_list():
    return render_template("admin_users.html",
                           users=User.query.all(),
                           roles=Role.query.all())

@admin_bp.post("/users/create")
def create_user():
    u = User(username=request.form["username"], email=request.form["email"])
    u.set_password(request.form.get("password","Init123!"))
    # 默认给普通角色
    role_user = Role.query.filter_by(name="user").first()
    if role_user: u.roles.append(role_user)
    db.session.add(u); db.session.commit()
    return redirect(url_for("admin.users_list"))

@admin_bp.post("/users/<int:uid>/grant")
def grant(uid):
    u = db.session.get(User, uid)
    r = Role.query.filter_by(name=request.form["role"]).first()
    if u and r and not u.has_role(r.name):
        u.roles.append(r); db.session.commit()
        flash(f"已授予用户 {u.username} {r.name} 权限", "success")
    return redirect(url_for("admin.users_list"))

from flask import flash, redirect, url_for

@admin_bp.post("/users/<int:uid>/revoke")
def revoke(uid):
    u = db.session.get(User, uid)
    # 自己撤自己 → 拦截并提示
    if u == current_user:
        flash("不能撤销自己的权限！", "error")
        return redirect(url_for("admin.users_list"))

    r = Role.query.filter_by(name=request.form["role"]).first()
    if u and r:
        # 从用户角色列表中剔除目标角色
        u.roles = [x for x in u.roles if x.id != r.id]
        db.session.commit()
        flash(f"已撤销用户 {u.username} 的 {r.name} 权限", "success")
    return redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/reset-password")
def reset(uid):
    u = db.session.get(User, uid)
    if u:
        u.set_password(request.form.get("new_password","Init123!")); db.session.commit()
    return redirect(url_for("admin.users_list"))
