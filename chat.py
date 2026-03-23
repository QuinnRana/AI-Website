# chat.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time
import random

@dataclass
class ChatAI:
    name: str = "Nova"
    history: List[Dict] = field(default_factory=list)

    # chat modes: "chat", "story_interactive", "story_read"
    mode: str = "chat"

    # story state
    story_step: int = 0
    story_vars: Dict = field(default_factory=dict)

    def intro(self) -> str:
        return (
            f"Hi — I’m {self.name}. "
            f"You can chat with me, or switch to Story mode (read-only or interactive)."
        )

    # --------- MODE CONTROL ----------
    def set_mode(self, mode: str):
        allowed = {"chat", "story_interactive", "story_read"}
        if mode not in allowed:
            mode = "chat"
        self.mode = mode
        # reset story when switching to a story mode
        if mode in {"story_interactive", "story_read"}:
            self.story_step = 0
            self.story_vars = {}

    def reset(self):
        self.history.clear()
        self.mode = "chat"
        self.story_step = 0
        self.story_vars = {}

    # --------- CORE RESPONSE ----------
    def respond(self, user_text: str) -> str:
        user_text = (user_text or "").strip()

        # store user msg if it's not empty (optional)
        if user_text:
            self.history.append({"role": "user", "text": user_text, "ts": time.time()})

        if self.mode == "chat":
            reply = self._chat_reply(user_text)
        elif self.mode == "story_read":
            # ignore user input; just advance story
            reply = self._story_next(answer=None)
        elif self.mode == "story_interactive":
            # use user input as answer when required
            reply = self._story_next(answer=user_text if user_text else None)
        else:
            reply = "I’m not sure what mode I’m in. Switching back to chat."
            self.mode = "chat"

        self.history.append({"role": "assistant", "text": reply, "ts": time.time()})
        return reply

    # --------- NORMAL CHAT ----------
    def _chat_reply(self, user_text: str) -> str:
        if not user_text:
            return "Say something and I’ll respond 🙂"

        lower = user_text.lower()
        if any(x in lower for x in ["hi", "hello", "hey"]):
            return f"Hey! I’m {self.name}. What’s up?"
        if "your name" in lower or "who are you" in lower:
            return f"My name is {self.name}. Want to chat or try Story mode?"
        if "what can you do" in lower:
            return "I can chat, and I also have a story mode where your answers change the plot."
        if "help" in lower:
            return "Try asking me anything, or switch to Story mode to read an adventure."

        # simple conversational fallback
        return f"Okay — tell me more about: “{user_text}”"

    # --------- STORY ENGINE ----------
    def _story_next(self, answer: Optional[str]) -> str:
        """
        story_step controls where we are in the story.
        story_vars stores choices: name, path, weapon, etc.
        """

        # Step 0: opening
        if self.story_step == 0:
            self.story_step = 1
            return (
                "📖 **Story: The Ashen Road**\n\n"
                "A black sky hangs over the ruined road. A lantern flickers in your hand.\n"
                "Somewhere ahead, something is watching.\n\n"
                "In interactive mode I’ll ask questions. In read-only mode, hit Next to continue."
            )

        # Step 1: ask name (interactive), or pick default (read-only)
        if self.story_step == 1:
            if self.mode == "story_read":
                self.story_vars["hero"] = "Traveler"
                self.story_step = 2
                return "You are known only as **Traveler**. You keep moving."
            else:
                if not answer:
                    return "What is your hero’s name?"
                self.story_vars["hero"] = answer[:24]
                self.story_step = 2
                return f"Alright. **{self.story_vars['hero']}**, you step forward and the road cracks under your boots."

        # Step 2: choose path
        if self.story_step == 2:
            if self.mode == "story_read":
                self.story_vars["path"] = "forest"
                self.story_step = 3
                return "You take the left path into the **crooked forest**. The trees whisper."
            else:
                if not answer:
                    return "Two paths split ahead: **forest** or **town**. Which do you choose?"
                pick = answer.lower()
                if "forest" in pick:
                    self.story_vars["path"] = "forest"
                elif "town" in pick:
                    self.story_vars["path"] = "town"
                else:
                    return "Pick **forest** or **town**."

                self.story_step = 3
                return f"You choose the **{self.story_vars['path']}**."

        # Step 3: first encounter
        if self.story_step == 3:
            hero = self.story_vars.get("hero", "Traveler")
            path = self.story_vars.get("path", "forest")

            if path == "forest":
                self.story_step = 4
                return (
                    f"In the forest, **{hero}** hears branches snap.\n"
                    "A **goblin scout** crawls from the brush, blade shaking.\n\n"
                    "Do you **talk**, **attack**, or **sneak away**?"
                )
            else:
                self.story_step = 4
                return (
                    f"The town gates are half-collapsed. **{hero}** steps over ash.\n"
                    "A pale figure watches from a rooftop — too still to be human.\n\n"
                    "Do you **call out**, **hide**, or **run**?"
                )

        # Step 4: resolve first choice
        if self.story_step == 4:
            if self.mode == "story_read":
                self.story_step = 5
                return "You keep your breathing steady and move with caution. The world feels… alive."
            else:
                if not answer:
                    return "Choose an action (example: talk / attack / sneak) and press Send."
                action = answer.lower()

                outcome = ""
                if "attack" in action or "run" in action:
                    outcome = "Your pulse spikes — you commit. The moment stretches, then snaps into motion."
                elif "talk" in action or "call" in action:
                    outcome = "You speak first. The air tightens. Sometimes words are sharper than steel."
                elif "hide" in action or "sneak" in action:
                    outcome = "You melt into the shadows. You weren’t born to die on someone else’s terms."
                else:
                    return "Try: **attack**, **talk**, **sneak**, **hide**, or **run**."

                self.story_vars["first_action"] = action
                self.story_step = 5
                return f"{outcome}\n\n✅ (Story continues… hit Send again to keep going.)"

        # Step 5+: placeholder continuation
        if self.story_step >= 5:
            self.story_step += 1
            hero = self.story_vars.get("hero", "Traveler")
            return (
                f"Chapter continues… **{hero}** walks deeper into the unknown.\n"
                "Soon we’ll hook this into the RPG battle system, inventory, quests, and saving."
            )
