from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ext import db
from models import User, Role, ResetToken, LoginLog

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
    u.set_password(request.form.get("password", "Init123!"))
    # 默认给普通角色
    role_user = Role.query.filter_by(name="user").first()
    if role_user: u.roles.append(role_user)
    db.session.add(u);
    db.session.commit()
    return redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/grant")
def grant(uid):
    u = db.session.get(User, uid)
    r = Role.query.filter_by(name=request.form["role"]).first()
    if u and r and not u.has_role(r.name):
        u.roles.append(r);
        db.session.commit()
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


@admin_bp.post("/users/<int:uid>/delete")
def delete(uid):
    u = db.session.get(User, uid)
    if not u:
        flash("目标用户不存在。", "error")
        return redirect(url_for("admin.users_list"))

    if u == current_user:
        flash("不能删除自己! ", category="error")
        return redirect(url_for("admin.users_list"))

    if u.has_role("admin"):
        admin_count = (
            User.query.join(User.roles)
            .filter(Role.name == "admin")
            .count()
        )
        if admin_count <= 1:
            flash("系统至少保留一名管理员，删除被阻止。", "error")
            return redirect(url_for("admin.users_list"))

    username = u.username  # 放到成功拿到 u 之后
    # —— 清理关联，避免外键约束问题（视你的级联配置而定）——
    u.roles.clear()  # 清 user↔role 关联行
    ResetToken.query.filter_by(user_id=uid).delete()  # 如果你不需要保留历史
    LoginLog.query.filter_by(user_id=uid).delete()  # 或者选择置空外键（看模型设计）

    db.session.delete(u)
    db.session.commit()
    flash(f"已删除用户 {username}！", "success")
    return redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/reset-password")
def reset(uid):
    u = db.session.get(User, uid)
    if u:
        u.set_password(request.form.get("new_password", "Init123!"));
        db.session.commit()
    return redirect(url_for("admin.users_list"))
