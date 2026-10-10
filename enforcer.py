"""The personality. STRESS is strict because it cares.

All templates are plain strings; ``line()`` fills whatever placeholders a
chosen line uses, so callers pass every key the pool might reference.
"""

import random

GREET_PENDING = [
    "Listen up, {name}. {remaining} questions stand between you and the exit.",
    "Back again, {name}. Good. The curriculum never sleeps.",
    "{name}. Quota's open. Let's find out what you remember.",
    "Welcome to your daily reckoning, {name}. {remaining} to go.",
]

GREET_DONE = [
    "Quota met. Anything beyond this point is voluntary growth. /more, if you dare.",
    "Daily quota complete. I'd say I'm proud, but I'm a state file with opinions.",
]

PRAISE = [
    "Correct. Don't get comfortable.",
    "Correct. The gradient approves.",
    "Right answer. Your streak survives another question.",
    "Acceptable. Barely.",
    "Correct. Somewhere, a loss function decreases in your honor.",
]

WRONG = [
    "WRONG. Again.",
    "No. Think, then type.",
    "Incorrect. Your future self is wincing.",
    "That's not it.",
    "Wrong. The exam will not be this patient.",
]

REVEAL = [
    "The answer was: {answer}.",
    "Time's up for this one. The answer: {answer}.",
]

SKIP = [
    "Skipped. Cowardice noted and logged.",
    "Fine. Skip. The question will be waiting tomorrow, and so will I.",
]

QUIT_DENIED = [
    "Denied. {remaining} question(s) remain between you and the exit.",
    "The exit is locked until the quota is met. {remaining} to go.",
    "You signed up for this. {remaining} left. /help if you're lost — not if you're soft.",
]

FAREWELL = [
    "Quota met. You're free. Same time tomorrow — I'll know if you don't show up.",
    "Go. Rest. Recover. And come back tomorrow, or the streak dies and we both know whose fault that is.",
]

STREAK_DIED = [
    "You vanished for {missed} day(s). Your {streak}-day streak is dead. We start from zero. Again.",
    "{missed} day(s) of silence. Streak: {streak} → 0. The syllabus noticed.",
]

MOTIVATION = [
    "Discipline is choosing what you want most over what you want now.",
    "You don't rise to your goals; you fall to the level of your preparation.",
    "Six months of focused reps can buy you ten years of freedom.",
    "The syllabus does not care about your mood. Neither do I.",
    "Pain is temporary. Failing the interview is public.",
    "Every question you skip was someone else's rep. They're ahead now.",
]

REDEMPTION_INTRO = [
    "Not so fast. You failed {count} question(s) today. We review failures here. Again:",
    "Before the ceremony: {count} failed question(s) demand a rematch.",
]

EXHAUSTED = [
    "You've exhausted my {subject} arsenal today. Recycling questions.",
    "Impressive drain of the {subject} pool. Round two, same questions.",
]

MIDNIGHT = [
    "Midnight crossed. A fresh day, a fresh quota. How convenient for you.",
]

DESERTER = "Deserting via EOF? Coward. Progress saved; your conscience was not."

INTERRUPT = "Ctrl+C won't save you. The quota remains."

# learner-agent attitude (the student bot gets the drill too)
LEARNER_STUDY = [
    "Browser open. The student works. You watch. Suddenly the roles feel dangerous?",
    "The child bot is reading now. Don't help it. That's how yours works too.",
    "Watch your agent sweat over a linked list. Then remember /quizme exists.",
]
LEARNER_DONE = [
    "The kid learned something today. Check /teach before it forgets plausibly.",
    "Session over. Reading the journal beats pretending you already know it.",
]


def line(pool, **kwargs):
    return random.choice(pool).format(**kwargs)
