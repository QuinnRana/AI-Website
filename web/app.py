import os
import sys
import json
import uuid
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

# Add project root (ai_bot) to Python path so imports work no matter where you run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from chat import ChatAI
from rpg.web_rpg import CLASSES, new_player, spawn_enemy, fight_turn, health_bar

AI_NAME = "Nova"

TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")
STATIC_DIR    = os.path.join(BASE_DIR, "web", "static")

UPLOAD_DIR    = os.path.join(BASE_DIR, "web", "uploads", "recordings")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "web", "uploads", "transcripts")
META_FILE     = os.path.join(BASE_DIR, "web", "uploads", "recordings_meta.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = "dev-secret-key"
app.permanent_session_lifetime = timedelta(days=7)

# One AI instance for the server (simple + works for your use-case)
nova = ChatAI(name=AI_NAME)


# ----------------------------
# Helpers
# ----------------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_meta():
    if not os.path.exists(META_FILE):
        return []
    with open(META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_meta(items):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def init_chat_session():
    session.permanent = True
    if "chat_mode" not in session:
        session["chat_mode"] = "chat"  # chat | story_read | story_interactive
    if "chat_history" not in session:
        session["chat_history"] = []   # [{"role":"user/ai","text":"..."}]


def build_context(history, limit=12):
    """
    If your ChatAI DOES NOT store history internally, we can include it in the prompt.
    This keeps conversation continuity.
    """
    history = history[-limit:]
    lines = []
    for m in history:
        who = "User" if m["role"] == "user" else AI_NAME
        lines.append(f"{who}: {m['text']}")
    return "\n".join(lines)


def respond_with_session(user_text: str) -> str:
    init_chat_session()

    mode = session["chat_mode"]
    history = session["chat_history"]

    # store user message
    history.append({"role": "user", "text": user_text})

    # set mode in AI (if your ChatAI supports it)
    try:
        nova.set_mode(mode)
    except Exception:
        pass

    # Provide context to AI so it can “remember” conversation
    context = build_context(history)
    prompt = (
        f"Mode: {mode}\n"
        f"Conversation so far:\n{context}\n\n"
        f"Now respond to the user's last message naturally."
    )

    reply = nova.respond(prompt)

    # store ai reply
    history.append({"role": "ai", "text": reply})
    session["chat_history"] = history

    return reply


# ----------------------------
# Pages
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html", ai_name=AI_NAME)


@app.route("/chat")
def chat_page():
    # This is your UI page; the JS should call /api/chat
    init_chat_session()
    return render_template("chat.html", ai_name=AI_NAME, history=session["chat_history"])


@app.route("/games")
def games():
    return render_template("games.html", ai_name=AI_NAME)


@app.route("/record")
def record():
    return render_template("record.html", ai_name=AI_NAME)


@app.route("/recordings")
def recordings():
    items = load_meta()
    return render_template("recordings.html", ai_name=AI_NAME, items=items)


@app.route("/recordings/<rid>")
def recording_detail(rid):
    items = load_meta()
    item = next((x for x in items if x["id"] == rid), None)
    if not item:
        return "Not found", 404

    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{rid}.txt")
    transcript = None
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()

    return render_template("recording_detail.html", ai_name=AI_NAME, item=item, transcript=transcript)


@app.route("/recordings/file/<path:filename>")
def recordings_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)


# ----------------------------
# Chat API
# ----------------------------
@app.route("/api/chat/intro")
def api_chat_intro():
    # What your UI calls on load
    try:
        return jsonify({"reply": nova.intro()})
    except Exception:
        return jsonify({"reply": f"Hi — I’m {AI_NAME}. Choose Chat or Story mode and type a message."})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"reply": ""})

    reply = respond_with_session(msg)
    return jsonify({"reply": reply})


@app.route("/api/mode", methods=["POST"])
def api_mode():
    init_chat_session()
    data = request.get_json(force=True) or {}
    mode = (data.get("mode") or "chat").strip()

    if mode not in ("chat", "story_read", "story_interactive"):
        mode = "chat"

    session["chat_mode"] = mode

    # optional: reset story state if your ChatAI uses it
    try:
        nova.set_mode(mode)
    except Exception:
        pass

    return jsonify({"ok": True, "mode": mode})


@app.route("/api/chat/reset", methods=["POST"])
def api_chat_reset():
    session.pop("chat_history", None)
    session.pop("chat_mode", None)
    try:
        nova.reset()
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/chat/clear", methods=["POST"])
def clear_chat():
    session.pop("chat_history", None)
    session.pop("chat_mode", None)
    return redirect(url_for("chat_page"))


# ----------------------------
# Recording Upload + Transcribe (stub)
# ----------------------------
@app.route("/record/upload", methods=["POST"])
def record_upload():
    if "audio" not in request.files:
        return jsonify({"error": "missing audio"}), 400

    audio = request.files["audio"]
    title = (request.form.get("title") or "").strip()

    rid = uuid.uuid4().hex[:10]
    filename = secure_filename(f"{rid}.webm")
    path = os.path.join(UPLOAD_DIR, filename)
    audio.save(path)

    items = load_meta()
    items.insert(0, {"id": rid, "title": title, "filename": filename, "created_at": now_str()})
    save_meta(items)

    return jsonify({"ok": True, "id": rid, "filename": filename})


@app.route("/recordings/<rid>/delete", methods=["POST"])
def recording_delete(rid):
    items = load_meta()
    item = next((x for x in items if x["id"] == rid), None)
    if not item:
        return redirect(url_for("recordings"))

    try:
        os.remove(os.path.join(UPLOAD_DIR, item["filename"]))
    except FileNotFoundError:
        pass

    try:
        os.remove(os.path.join(TRANSCRIPT_DIR, f"{rid}.txt"))
    except FileNotFoundError:
        pass

    items = [x for x in items if x["id"] != rid]
    save_meta(items)
    return redirect(url_for("recordings"))


@app.route("/recordings/<rid>/transcribe", methods=["POST"])
def recording_transcribe(rid):
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{rid}.txt")
    if not os.path.exists(transcript_path):
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("Transcription feature is not enabled yet.\n")
            f.write("Next step: wire Whisper to generate transcripts.\n")
    return redirect(url_for("recording_detail", rid=rid))


# ----------------------------
# RPG
# ----------------------------
@app.route("/games/rpg", methods=["GET", "POST"])
def rpg_home():
    if "rpg_player" not in session:
        return redirect(url_for("rpg_start"))

    if "rpg_enemy" not in session:
        session["rpg_enemy"] = spawn_enemy()

    player = session["rpg_player"]
    enemy = session["rpg_enemy"]

    if request.method == "POST":
        outcome = fight_turn(player, enemy)

        if outcome == "enemy_dead":
            session["rpg_enemy"] = spawn_enemy()
            enemy = session["rpg_enemy"]

        if outcome == "player_dead":
            session.pop("rpg_player", None)
            session.pop("rpg_enemy", None)
            return redirect(url_for("rpg_start"))

        session["rpg_player"] = player
        session["rpg_enemy"] = enemy
        return redirect(url_for("rpg_home"))

    return render_template(
        "rpg.html",
        ai_name=AI_NAME,
        player=player,
        enemy=enemy,
        pbar=health_bar(player["hp"], player["max_hp"]),
        ebar=health_bar(enemy["hp"], enemy["max_hp"]),
    )


@app.route("/games/rpg/start", methods=["GET", "POST"])
def rpg_start():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        job = (request.form.get("job") or "Crusader").strip()
        session["rpg_player"] = new_player(name, job)
        session["rpg_enemy"] = spawn_enemy()
        return redirect(url_for("rpg_home"))

    return render_template("rpg_start.html", ai_name=AI_NAME, classes=list(CLASSES.keys()))


@app.route("/games/rpg/reset", methods=["POST"])
def rpg_reset():
    session.pop("rpg_player", None)
    session.pop("rpg_enemy", None)
    return redirect(url_for("rpg_start"))


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
