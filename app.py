"""
╔══════════════════════════════════════════════════════════╗
║        KADAM SOS FOUNDATION — app.py                     ║
║  Three-tier security: Regular | Auth Code | Masterkey    ║
╚══════════════════════════════════════════════════════════╝
"""

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, flash
)
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import json, os, uuid

app = Flask(__name__)
app.secret_key = "kadam_secret_xK9#mP2@qL7"   # change in production!

# ─────────────────────────────────────────────
# FILE UPLOAD CONFIG
# ─────────────────────────────────────────────
UPLOAD_FOLDER      = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024   # 5 MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_photo(field_name="photo"):
    """Save an uploaded image and return its static path, or empty string."""
    f = request.files.get(field_name)
    if not f or f.filename == "" or not allowed_file(f.filename):
        return ""
    ext      = f.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_FOLDER, filename))
    return f"uploads/{filename}"


# ─────────────────────────────────────────────
# PERSISTENT JSON STORAGE
# ─────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

DEFAULT_STATE = {
    "regular_password": "kadam2024",
    "auth_code":        "KADAM@auth",
    "stats": {"cities": 11, "events": 149, "members": 535, "causes": 5},
    # instagram_posts: [{url, name, thumbnail}] x3
    "instagram_posts": [
        {"url": "", "name": "Post 1", "thumbnail": ""},
        {"url": "", "name": "Post 2", "thumbnail": ""},
        {"url": "", "name": "Post 3", "thumbnail": ""},
    ],
    "volunteer_apps": [],
    "contact_msgs":   [],
    # Team data
    # member schema: {id, name, role, bio, photo, photo_visible, socials:[{platform,url,handle,visible}×2], order}
    "main_members": [],
    # branch schema: {id, name, city, lat, lng, order, board:[], volunteers:[]}
    "branches": [],
    # program schema: {id, name, description, category, thumbnail, founder_name,
    #                  founder_statement, position, content_file, content_type, created_at}
    "programs": [],
    # stories: single uploaded file shown full screen
    "stories_file": "",
    "stories_type": "",
    # hero carousel images
    "hero_images": [],
    # story cards on home page (3 cards, each with own images)
    "story_cards": [
        {"tag": "Education",          "title": "Books for Every Child",         "excerpt": "Our volunteers distributed stationery and ran interactive sessions with 200+ children in government schools.", "images": []},
        {"tag": "Environment",         "title": "Cleaning the Streets of Bhopal","excerpt": "80+ volunteers joined our city-wide cleanliness drive and planted saplings across public spaces.",          "images": []},
        {"tag": "Women Empowerment",   "title": "Skills That Changed Lives",     "excerpt": "35 women gained vocational skills and found employment through our workshop program.",                        "images": []}
    ],
}


def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, val in DEFAULT_STATE.items():
                if key not in data:
                    data[key] = val
                elif isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        if sub_key not in data[key]:
                            data[key][sub_key] = sub_val
            return data
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_STATE)


def save_state():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except IOError as e:
        app.logger.error("Could not save state: %s", e)


state = load_state()


@app.context_processor
def inject_state():
    return dict(state=state)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def next_id(collection):
    return max((item["id"] for item in collection), default=0) + 1


def find_branch(bid):
    return next((b for b in state["branches"] if b["id"] == bid), None)


def find_member(collection, mid):
    return next((m for m in collection if m["id"] == mid), None)


def move_item(collection, item_id, direction):
    """Swap the item with its neighbour in the given direction (-1=up, 1=down)."""
    col = sorted(collection, key=lambda x: x.get("order", 0))
    idx = next((i for i, x in enumerate(col) if x["id"] == item_id), None)
    if idx is None:
        return
    swap = idx + direction
    if 0 <= swap < len(col):
        col[idx]["order"], col[swap]["order"] = col[swap]["order"], col[idx]["order"]


def parse_member_form():
    """Extract member fields from request.form + photo upload.
    Social slots: two slots, each with platform, url, handle, visible.
    Photo: uploaded file + photo_visible toggle.
    """
    photo      = save_uploaded_photo("photo")
    photo_vis  = request.form.get("photo_visible", "0") == "1"
    socials = []
    for i in (1, 2):
        platform = request.form.get(f"social_{i}_platform", "").strip()
        url      = request.form.get(f"social_{i}_url",      "").strip()
        handle   = request.form.get(f"social_{i}_handle",   "").strip()
        visible  = request.form.get(f"social_{i}_visible", "0") == "1"
        socials.append({
            "platform": platform,
            "url":      url,
            "handle":   handle,
            "visible":  visible,
        })
    return {
        "name":          request.form.get("name", "").strip(),
        "role":          request.form.get("role", "").strip(),
        "bio":           request.form.get("bio",  "").strip(),
        "photo":         photo,
        "photo_visible": photo_vis,
        "socials":       socials,
    }


# ─────────────────────────────────────────────
# MASTERKEY
# ─────────────────────────────────────────────
def compute_masterkey(date=None):
    d         = date or datetime.now()
    date_str  = d.strftime("%d%m%Y")
    digit_sum = sum(int(c) for c in date_str)
    return f"lsfs,kadam{digit_sum * 123}"


LOGIN_REGULAR   = "regular"
LOGIN_MASTERKEY = "masterkey"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("admin_logged_in") not in (LOGIN_REGULAR, LOGIN_MASTERKEY):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def masterkey_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("admin_logged_in") != LOGIN_MASTERKEY:
            flash("This section requires Masterkey access.", "error")
            return redirect(url_for("admin_dashboard"))
        return f(*args, **kwargs)
    return decorated


# ═════════════════════════════════════════════
#  PUBLIC ROUTES
# ═════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("index.html",
        stats=state["stats"],
        hero_images=state.get("hero_images", []),
        story_cards=state.get("story_cards", []),
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/volunteer")
def volunteer():
    return render_template("volunteer.html")

@app.route("/donate")
def donate():
    return render_template("donate.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/team")
def team():
    main_members = sorted(state["main_members"], key=lambda x: x.get("order", 0))
    branches     = sorted(state["branches"],     key=lambda x: x.get("order", 0))
    return render_template("team.html", main_members=main_members, branches=branches)


# ═════════════════════════════════════════════
#  PUBLIC APIs
# ═════════════════════════════════════════════

@app.route("/api/stats")
def api_stats():
    return jsonify(state["stats"])


@app.route("/api/instagram")
def api_instagram():
    """Return the 3 Instagram posts as {url, name, thumbnail, configured}."""
    posts = state.get("instagram_posts", [])
    result = []
    for p in posts:
        if isinstance(p, str):
            result.append({"url": p, "name": "", "thumbnail": "", "configured": bool(p and "PLACEHOLDER" not in p)})
        else:
            result.append({
                "url":        p.get("url", ""),
                "name":       p.get("name", ""),
                "thumbnail":  p.get("thumbnail", ""),
                "configured": bool(p.get("url") and "PLACEHOLDER" not in p.get("url", "")),
            })
    return jsonify(result)


@app.route("/api/volunteer", methods=["POST"])
def api_volunteer():
    data = request.get_json()
    for field in ["name", "email", "city", "cause"]:
        if not data.get(field):
            return jsonify({"success": False, "error": f"'{field}' is required."}), 400
    entry = {
        "id":        next_id(state["volunteer_apps"]),
        "name":      data["name"].strip(),
        "email":     data["email"].strip().lower(),
        "phone":     data.get("phone", "").strip(),
        "city":      data["city"].strip(),
        "cause":     data["cause"],
        "message":   data.get("message", "").strip(),
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "reviewed":  False,
    }
    state["volunteer_apps"].append(entry)
    save_state()
    return jsonify({"success": True, "message": f"Welcome, {entry['name']}! We'll be in touch soon."})


@app.route("/api/support", methods=["POST"])
def api_support():
    """Women's support / help request — stored as contact message with category."""
    data = request.get_json()
    for field in ["name", "contact", "issue", "description"]:
        if not data.get(field):
            return jsonify({"success": False, "error": f"'{field}' is required."}), 400
    entry = {
        "id":        next_id(state["contact_msgs"]),
        "name":      data["name"].strip(),
        "email":     data["contact"].strip(),   # contact = phone or email
        "subject":   f"🆘 Support Request — {data['issue'].strip()}",
        "message":   data["description"].strip(),
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "read":      False,
    }
    state["contact_msgs"].append(entry)
    save_state()
    return jsonify({"success": True, "message": "Your request has been received. We will reach out to you soon."})


@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json()
    for field in ["name", "email", "message"]:
        if not data.get(field):
            return jsonify({"success": False, "error": f"'{field}' is required."}), 400
    entry = {
        "id":        next_id(state["contact_msgs"]),
        "name":      data["name"].strip(),
        "email":     data["email"].strip().lower(),
        "subject":   data.get("subject", "General Enquiry").strip(),
        "message":   data["message"].strip(),
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "read":      False,
    }
    state["contact_msgs"].append(entry)
    save_state()
    return jsonify({"success": True, "message": "Thank you! We'll get back to you within 48 hours."})


@app.route("/api/branches")
def api_branches():
    """Branch data for the team page map."""
    branches = sorted(state["branches"], key=lambda x: x.get("order", 0))
    return jsonify([{
        "id":         b["id"],
        "name":       b["name"],
        "city":       b["city"],
        "lat":        b["lat"],
        "lng":        b["lng"],
        "board":      sorted(b.get("board",      []), key=lambda x: x.get("order", 0)),
        "volunteers": sorted(b.get("volunteers", []), key=lambda x: x.get("order", 0)),
    } for b in branches])


# ═════════════════════════════════════════════
#  ADMIN — AUTH
# ═════════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in") in (LOGIN_REGULAR, LOGIN_MASTERKEY):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        pw = request.form.get("password", "").strip()
        if pw == state["regular_password"]:
            session["admin_logged_in"] = LOGIN_REGULAR
            session["admin_name"]      = "Admin"
            return redirect(url_for("admin_dashboard"))
        elif pw == compute_masterkey():
            session["admin_logged_in"] = LOGIN_MASTERKEY
            session["admin_name"]      = "Founder"
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Incorrect password. Please try again."
    return render_template("admin/login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/change-password", methods=["GET", "POST"])
def admin_change_password():
    if request.method == "POST":
        if request.form.get("auth_code", "").strip() == state["auth_code"]:
            session["auth_unlocked"] = True
            return redirect(url_for("admin_set_password"))
        return render_template("admin/change_password.html", error="Incorrect auth code.")
    return render_template("admin/change_password.html", error=None)


@app.route("/admin/set-password", methods=["GET", "POST"])
def admin_set_password():
    if not session.get("auth_unlocked"):
        return redirect(url_for("admin_change_password"))
    if request.method == "POST":
        new_pass = request.form.get("new_password", "").strip()
        confirm  = request.form.get("confirm_password", "").strip()
        if len(new_pass) < 6:
            return render_template("admin/set_password.html", error="Minimum 6 characters.")
        if new_pass != confirm:
            return render_template("admin/set_password.html", error="Passwords do not match.")
        state["regular_password"] = new_pass
        save_state()
        session.pop("auth_unlocked", None)
        flash("Password updated successfully!", "success")
        return redirect(url_for("admin_login"))
    return render_template("admin/set_password.html", error=None)


# ═════════════════════════════════════════════
#  ADMIN — DASHBOARD & EXISTING SECTIONS
# ═════════════════════════════════════════════

@app.route("/admin")
@login_required
def admin_dashboard():
    is_master   = session.get("admin_logged_in") == LOGIN_MASTERKEY
    unread_msgs = sum(1 for m in state["contact_msgs"]   if not m["read"])
    unreviewed  = sum(1 for v in state["volunteer_apps"] if not v["reviewed"])
    return render_template("admin/dashboard.html",
        is_master=is_master, stats=state["stats"],
        instagram_posts=state.get("instagram_posts", []),
        volunteer_count=len(state["volunteer_apps"]),
        contact_count=len(state["contact_msgs"]),
        unread_msgs=unread_msgs, unreviewed=unreviewed,
    )


@app.route("/admin/instagram", methods=["GET", "POST"])
@login_required
def admin_instagram():
    if request.method == "POST":
        posts = []
        for i in (1, 2, 3):
            thumb = save_uploaded_photo(f"thumbnail_{i}")
            existing = state.get("instagram_posts", [{}, {}, {}])
            old_thumb = existing[i-1].get("thumbnail", "") if len(existing) >= i else ""
            posts.append({
                "url":       request.form.get(f"url{i}", "").strip(),
                "name":      request.form.get(f"name{i}", "").strip(),
                "thumbnail": thumb if thumb else old_thumb,
            })
        state["instagram_posts"] = posts
        save_state()
        flash("Instagram posts updated!", "success")
        return redirect(url_for("admin_instagram"))
    posts = state.get("instagram_posts", [
        {"url":"","name":"","thumbnail":""},
        {"url":"","name":"","thumbnail":""},
        {"url":"","name":"","thumbnail":""},
    ])
    return render_template("admin/instagram.html", posts=posts)


@app.route("/admin/stats", methods=["GET", "POST"])
@login_required
def admin_stats():
    if request.method == "POST":
        try:
            for key in ["cities", "events", "members", "causes"]:
                state["stats"][key] = int(request.form.get(key, 0))
            save_state()
            flash("Stats updated!", "success")
        except ValueError:
            flash("Please enter valid numbers.", "error")
        return redirect(url_for("admin_stats"))
    return render_template("admin/stats.html", stats=state["stats"])


@app.route("/admin/volunteers")
@login_required
def admin_volunteers():
    return render_template("admin/volunteers.html", apps=list(reversed(state["volunteer_apps"])))

@app.route("/admin/volunteers/<int:vid>/review", methods=["POST"])
@login_required
def admin_review_volunteer(vid):
    for a in state["volunteer_apps"]:
        if a["id"] == vid:
            a["reviewed"] = not a["reviewed"]; save_state(); break
    return jsonify({"success": True})

@app.route("/admin/volunteers/<int:vid>/delete", methods=["POST"])
@login_required
def admin_delete_volunteer(vid):
    state["volunteer_apps"] = [a for a in state["volunteer_apps"] if a["id"] != vid]
    save_state()
    return jsonify({"success": True})


@app.route("/admin/messages")
@login_required
def admin_messages():
    return render_template("admin/messages.html", msgs=list(reversed(state["contact_msgs"])))

@app.route("/admin/messages/<int:mid>/read", methods=["POST"])
@login_required
def admin_mark_read(mid):
    for m in state["contact_msgs"]:
        if m["id"] == mid:
            m["read"] = not m["read"]; save_state(); break
    return jsonify({"success": True})

@app.route("/admin/messages/<int:mid>/delete", methods=["POST"])
@login_required
def admin_delete_message(mid):
    state["contact_msgs"] = [m for m in state["contact_msgs"] if m["id"] != mid]
    save_state()
    return jsonify({"success": True})


@app.route("/admin/change-authcode", methods=["GET", "POST"])
@masterkey_required
def admin_change_authcode():
    if request.method == "POST":
        new_code = request.form.get("new_auth_code", "").strip()
        confirm  = request.form.get("confirm_auth_code", "").strip()
        if len(new_code) < 6:
            return render_template("admin/change_authcode.html", error="Minimum 6 characters.")
        if new_code != confirm:
            return render_template("admin/change_authcode.html", error="Codes do not match.")
        state["auth_code"] = new_code
        save_state()
        flash("Auth code updated!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/change_authcode.html", error=None)


# ═════════════════════════════════════════════
#  ADMIN — TEAM MANAGEMENT
# ═════════════════════════════════════════════

@app.route("/admin/team")
@login_required
def admin_team():
    main_members = sorted(state["main_members"], key=lambda x: x.get("order", 0))
    branches     = sorted(state["branches"],     key=lambda x: x.get("order", 0))
    return render_template("admin/team.html", main_members=main_members, branches=branches)


# ── Main body members ──

@app.route("/admin/team/members/add", methods=["POST"])
@login_required
def admin_add_main_member():
    data   = parse_member_form()
    member = {"id": next_id(state["main_members"]), "order": len(state["main_members"]), **data}
    state["main_members"].append(member)
    save_state()
    flash(f"Added {member['name']} to main body.", "success")
    return redirect(url_for("admin_team"))


@app.route("/admin/team/members/<int:mid>/edit", methods=["POST"])
@login_required
def admin_edit_main_member(mid):
    member = find_member(state["main_members"], mid)
    if not member:
        flash("Member not found.", "error")
        return redirect(url_for("admin_team"))
    data = parse_member_form()
    member["name"]          = data["name"] or member["name"]
    member["role"]          = data["role"]
    member["bio"]           = data["bio"]
    member["photo_visible"] = data["photo_visible"]
    member["socials"]       = data["socials"]
    if data["photo"]:
        member["photo"] = data["photo"]
    save_state()
    flash("Member updated.", "success")
    return redirect(url_for("admin_team"))


@app.route("/admin/team/members/<int:mid>/delete", methods=["POST"])
@login_required
def admin_delete_main_member(mid):
    state["main_members"] = [m for m in state["main_members"] if m["id"] != mid]
    save_state()
    flash("Member deleted.", "success")
    return redirect(url_for("admin_team"))


@app.route("/admin/team/members/<int:mid>/move/<direction>", methods=["POST"])
@login_required
def admin_move_main_member(mid, direction):
    move_item(state["main_members"], mid, -1 if direction == "up" else 1)
    save_state()
    return redirect(url_for("admin_team"))


# ── Branches ──

@app.route("/admin/team/branches/add", methods=["POST"])
@login_required
def admin_add_branch():
    try:
        lat = float(request.form.get("lat", 0))
        lng = float(request.form.get("lng", 0))
    except ValueError:
        flash("Invalid coordinates.", "error")
        return redirect(url_for("admin_team"))
    branch = {
        "id":    next_id(state["branches"]),
        "name":  request.form.get("name", "").strip(),
        "city":  request.form.get("city", "").strip(),
        "lat":   lat, "lng": lng,
        "order": len(state["branches"]),
        "board": [], "volunteers": [],
    }
    state["branches"].append(branch)
    save_state()
    flash(f"Branch '{branch['name']}' added.", "success")
    return redirect(url_for("admin_team"))


@app.route("/admin/team/branches/<int:bid>/edit", methods=["POST"])
@login_required
def admin_edit_branch(bid):
    branch = find_branch(bid)
    if not branch:
        flash("Branch not found.", "error")
        return redirect(url_for("admin_team"))
    try:
        branch["lat"] = float(request.form.get("lat", branch["lat"]))
        branch["lng"] = float(request.form.get("lng", branch["lng"]))
    except ValueError:
        flash("Invalid coordinates.", "error")
        return redirect(url_for("admin_team"))
    branch["name"] = request.form.get("name", branch["name"]).strip()
    branch["city"] = request.form.get("city", branch["city"]).strip()
    save_state()
    flash("Branch updated.", "success")
    return redirect(url_for("admin_team"))


@app.route("/admin/team/branches/<int:bid>/delete", methods=["POST"])
@login_required
def admin_delete_branch(bid):
    state["branches"] = [b for b in state["branches"] if b["id"] != bid]
    save_state()
    flash("Branch deleted.", "success")
    return redirect(url_for("admin_team"))


@app.route("/admin/team/branches/<int:bid>/move/<direction>", methods=["POST"])
@login_required
def admin_move_branch(bid, direction):
    move_item(state["branches"], bid, -1 if direction == "up" else 1)
    save_state()
    return redirect(url_for("admin_team"))


# ── Branch members shared logic ──

def _add_branch_member(bid, role_key):
    branch = find_branch(bid)
    if not branch:
        flash("Branch not found.", "error")
        return redirect(url_for("admin_team"))
    collection = branch[role_key]
    data   = parse_member_form()
    member = {"id": next_id(collection), "order": len(collection), **data}
    collection.append(member)
    save_state()
    flash(f"Added {member['name']}.", "success")
    return redirect(url_for("admin_team") + f"#branch-{bid}")


def _edit_branch_member(bid, role_key, mid):
    branch = find_branch(bid)
    if not branch:
        flash("Branch not found.", "error")
        return redirect(url_for("admin_team"))
    member = find_member(branch[role_key], mid)
    if not member:
        flash("Member not found.", "error")
        return redirect(url_for("admin_team"))
    data = parse_member_form()
    member["name"]          = data["name"] or member["name"]
    member["role"]          = data["role"]
    member["bio"]           = data["bio"]
    member["photo_visible"] = data["photo_visible"]
    member["socials"]       = data["socials"]
    if data["photo"]:
        member["photo"] = data["photo"]
    save_state()
    flash("Member updated.", "success")
    return redirect(url_for("admin_team") + f"#branch-{bid}")


def _delete_branch_member(bid, role_key, mid):
    branch = find_branch(bid)
    if not branch:
        flash("Branch not found.", "error")
        return redirect(url_for("admin_team"))
    branch[role_key] = [m for m in branch[role_key] if m["id"] != mid]
    save_state()
    flash("Member deleted.", "success")
    return redirect(url_for("admin_team"))


def _move_branch_member(bid, role_key, mid, direction):
    branch = find_branch(bid)
    if not branch:
        flash("Branch not found.", "error")
        return redirect(url_for("admin_team"))
    move_item(branch[role_key], mid, -1 if direction == "up" else 1)
    save_state()
    return redirect(url_for("admin_team"))


# Board members
@app.route("/admin/team/branches/<int:bid>/board/add", methods=["POST"])
@login_required
def admin_add_board_member(bid):
    return _add_branch_member(bid, "board")

@app.route("/admin/team/branches/<int:bid>/board/<int:mid>/edit", methods=["POST"])
@login_required
def admin_edit_board_member(bid, mid):
    return _edit_branch_member(bid, "board", mid)

@app.route("/admin/team/branches/<int:bid>/board/<int:mid>/delete", methods=["POST"])
@login_required
def admin_delete_board_member(bid, mid):
    return _delete_branch_member(bid, "board", mid)

@app.route("/admin/team/branches/<int:bid>/board/<int:mid>/move/<direction>", methods=["POST"])
@login_required
def admin_move_board_member(bid, mid, direction):
    return _move_branch_member(bid, "board", mid, direction)


# Branch volunteers
@app.route("/admin/team/branches/<int:bid>/volunteers/add", methods=["POST"])
@login_required
def admin_add_branch_volunteer(bid):
    return _add_branch_member(bid, "volunteers")

@app.route("/admin/team/branches/<int:bid>/volunteers/<int:mid>/edit", methods=["POST"])
@login_required
def admin_edit_branch_volunteer(bid, mid):
    return _edit_branch_member(bid, "volunteers", mid)

@app.route("/admin/team/branches/<int:bid>/volunteers/<int:mid>/delete", methods=["POST"])
@login_required
def admin_delete_branch_volunteer(bid, mid):
    return _delete_branch_member(bid, "volunteers", mid)

@app.route("/admin/team/branches/<int:bid>/volunteers/<int:mid>/move/<direction>", methods=["POST"])
@login_required
def admin_move_branch_volunteer(bid, mid, direction):
    return _move_branch_member(bid, "volunteers", mid, direction)


# ═════════════════════════════════════════════
#  PUBLIC — PROGRAMS & STORIES
# ═════════════════════════════════════════════

PROGRAM_CATEGORIES = [
    "Education", "Women Empowerment", "Youth Welfare",
    "Environment", "Animal Welfare", "Misc"
]

@app.route("/programs")
def programs():
    progs = sorted(state["programs"], key=lambda x: (x.get("position", 999), x.get("id", 0)))
    return render_template("programs.html", programs=progs, categories=PROGRAM_CATEGORIES)

@app.route("/programs/<int:pid>/view")
def program_view(pid):
    prog = next((p for p in state["programs"] if p["id"] == pid), None)
    if not prog or not prog.get("content_file"):
        return "No content uploaded for this program.", 404
    return render_template("program_view.html", program=prog)

@app.route("/stories")
def stories():
    return render_template("stories.html",
                           stories_file=state.get("stories_file", ""),
                           stories_type=state.get("stories_type", ""))


# ═════════════════════════════════════════════
#  ADMIN — PROGRAMS
# ═════════════════════════════════════════════

@app.route("/admin/programs")
@login_required
def admin_programs():
    progs = sorted(state["programs"], key=lambda x: (x.get("position", 999), x.get("id", 0)))
    return render_template("admin/programs.html",
                           programs=progs,
                           categories=PROGRAM_CATEGORIES)


@app.route("/admin/programs/add", methods=["POST"])
@login_required
def admin_add_program():
    thumbnail    = save_uploaded_photo("thumbnail")
    content_file = _save_program_file("content_file")
    try:
        position = int(request.form.get("position", 99))
    except ValueError:
        position = 99

    prog = {
        "id":                next_id(state["programs"]),
        "name":              request.form.get("name", "").strip(),
        "description":       request.form.get("description", "").strip(),
        "category":          request.form.get("category", "Misc").strip(),
        "thumbnail":         thumbnail,
        "founder_name":      request.form.get("founder_name", "").strip(),
        "founder_statement": request.form.get("founder_statement", "").strip(),
        "position":          position,
        "content_file":      content_file,
        "content_type":      _file_type(content_file),
        "created_at":        datetime.now().strftime("%d %b %Y"),
    }
    state["programs"].append(prog)
    save_state()
    flash(f"Program '{prog['name']}' added.", "success")
    return redirect(url_for("admin_programs"))


@app.route("/admin/programs/<int:pid>/edit", methods=["POST"])
@login_required
def admin_edit_program(pid):
    prog = next((p for p in state["programs"] if p["id"] == pid), None)
    if not prog:
        flash("Program not found.", "error")
        return redirect(url_for("admin_programs"))

    thumbnail    = save_uploaded_photo("thumbnail")
    content_file = _save_program_file("content_file")
    try:
        position = int(request.form.get("position", prog.get("position", 99)))
    except ValueError:
        position = prog.get("position", 99)

    prog["name"]              = request.form.get("name", prog["name"]).strip()
    prog["description"]       = request.form.get("description", prog["description"]).strip()
    prog["category"]          = request.form.get("category", prog["category"]).strip()
    prog["founder_name"]      = request.form.get("founder_name", prog.get("founder_name", "")).strip()
    prog["founder_statement"] = request.form.get("founder_statement", prog.get("founder_statement", "")).strip()
    prog["position"]          = position
    if thumbnail:
        prog["thumbnail"] = thumbnail
    if content_file:
        prog["content_file"] = content_file
        prog["content_type"] = _file_type(content_file)

    save_state()
    flash("Program updated.", "success")
    return redirect(url_for("admin_programs"))


@app.route("/admin/programs/<int:pid>/delete", methods=["POST"])
@login_required
def admin_delete_program(pid):
    state["programs"] = [p for p in state["programs"] if p["id"] != pid]
    save_state()
    flash("Program deleted.", "success")
    return redirect(url_for("admin_programs"))


# ── Stories upload ──
@app.route("/admin/stories", methods=["GET", "POST"])
@login_required
def admin_stories():
    if request.method == "POST":
        f = request.files.get("stories_file")
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower()
            if ext in ("html", "htm", "pdf"):
                filename = f"stories_{uuid.uuid4().hex}.{ext}"
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                state["stories_file"] = f"uploads/{filename}"
                state["stories_type"] = "pdf" if ext == "pdf" else "html"
                save_state()
                flash("Stories file uploaded successfully!", "success")
            else:
                flash("Only HTML or PDF files allowed.", "error")
        return redirect(url_for("admin_stories"))
    return render_template("admin/stories.html",
                           stories_file=state.get("stories_file", ""),
                           stories_type=state.get("stories_type", ""))


# ── Program file helpers ──
def _save_program_file(field_name):
    """Save an HTML or PDF program content file, return its path."""
    f = request.files.get(field_name)
    if not f or f.filename == "":
        return ""
    ext = f.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("html", "htm", "pdf"):
        return ""
    filename = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_FOLDER, filename))
    return f"uploads/{filename}"

def _file_type(path):
    if not path:
        return ""
    ext = path.rsplit(".", 1)[-1].lower()
    return "pdf" if ext == "pdf" else "html"


# ═════════════════════════════════════════════
#  ADMIN — MEDIA (hero images + story card images)
# ═════════════════════════════════════════════

@app.route("/admin/media")
@login_required
def admin_media():
    return render_template("admin/media.html",
        hero_images=state.get("hero_images", []),
        story_cards=state.get("story_cards", []),
    )


@app.route("/admin/media/hero/upload", methods=["POST"])
@login_required
def admin_hero_upload():
    files = request.files.getlist("images")
    added = 0
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            ext = f.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            state.setdefault("hero_images", []).append(f"uploads/{filename}")
            added += 1
    save_state()
    flash(f"{added} hero image(s) uploaded.", "success")
    return redirect(url_for("admin_media"))


@app.route("/admin/media/hero/delete", methods=["POST"])
@login_required
def admin_hero_delete():
    img_path = request.form.get("image", "")
    images   = state.get("hero_images", [])
    if img_path in images:
        images.remove(img_path)
        state["hero_images"] = images
        save_state()
        flash("Hero image removed.", "success")
    return redirect(url_for("admin_media"))


@app.route("/admin/media/story/<int:card_idx>/upload", methods=["POST"])
@login_required
def admin_story_card_upload(card_idx):
    cards = state.get("story_cards", [])
    if card_idx < 0 or card_idx >= len(cards):
        flash("Invalid card index.", "error")
        return redirect(url_for("admin_media"))
    files = request.files.getlist("images")
    added = 0
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            ext = f.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            cards[card_idx].setdefault("images", []).append(f"uploads/{filename}")
            added += 1
    save_state()
    flash(f"{added} image(s) uploaded to story card {card_idx + 1}.", "success")
    return redirect(url_for("admin_media"))


@app.route("/admin/media/story/<int:card_idx>/delete", methods=["POST"])
@login_required
def admin_story_card_delete(card_idx):
    cards = state.get("story_cards", [])
    if card_idx < 0 or card_idx >= len(cards):
        flash("Invalid card index.", "error")
        return redirect(url_for("admin_media"))
    img_path = request.form.get("image", "")
    images   = cards[card_idx].get("images", [])
    if img_path in images:
        images.remove(img_path)
        cards[card_idx]["images"] = images
        save_state()
        flash("Story card image removed.", "success")
    return redirect(url_for("admin_media"))


@app.route("/admin/media/story/<int:card_idx>/edit", methods=["POST"])
@login_required
def admin_story_card_edit(card_idx):
    cards = state.get("story_cards", [])
    if card_idx < 0 or card_idx >= len(cards):
        flash("Invalid card index.", "error")
        return redirect(url_for("admin_media"))
    cards[card_idx]["tag"]     = request.form.get("tag",     cards[card_idx].get("tag", "")).strip()
    cards[card_idx]["title"]   = request.form.get("title",   cards[card_idx].get("title", "")).strip()
    cards[card_idx]["excerpt"] = request.form.get("excerpt", cards[card_idx].get("excerpt", "")).strip()
    save_state()
    flash(f"Story card {card_idx + 1} updated.", "success")
    return redirect(url_for("admin_media"))


# ═════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000)
