import re


EMOTION_KEYWORDS = {
    "happy": ("happy", "great", "excited", "proud", "wonderful", "glad", "joyful"),
    "sad": ("sad", "upset", "lonely", "disappointed", "unhappy", "down", "hurt"),
    "angry": ("angry", "mad", "annoyed", "frustrated", "furious", "irritated"),
    "anxious": ("anxious", "worried", "nervous", "scared", "afraid", "stressed", "overwhelmed"),
    "confused": ("confused", "unsure", "don't understand", "do not understand", "lost"),
}

RESPONSES = {
    "happy": "That sounds lovely! What happened that made you feel this way?",
    "sad": "I'm sorry things feel difficult right now. Would you like to tell me more?",
    "angry": "It sounds like something has really frustrated you. What happened?",
    "anxious": "That sounds stressful. What is worrying you most right now?",
    "confused": "It's okay to feel unsure. Which part would you like to talk through?",
    "neutral": "I'm here to listen. How are you feeling today?",
}


def detect_emotion(message):
    text = message.lower()
    scores = {
        emotion: sum(
            bool(re.search(r"\b" + re.escape(keyword) + r"\b", text))
            for keyword in keywords
        )
        for emotion, keywords in EMOTION_KEYWORDS.items()
    }
    emotion = max(scores, key=scores.get)
    return emotion if scores[emotion] else "neutral"


def main():
    print("SOULMATE: Hi! I'm here to chat. Tell me what's on your mind.")
    print("SOULMATE: Type 'quit' or 'exit' whenever you want to leave.")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSOULMATE: Goodbye. Take care!")
            break

        if message.lower() in {"quit", "exit", "bye"}:
            print("SOULMATE: Goodbye. Take care!")
            break

        if not message:
            print("SOULMATE: Whenever you're ready, tell me what's on your mind.")
            continue

        emotion = detect_emotion(message)
        print(f"SOULMATE: {RESPONSES[emotion]}")


if __name__ == "__main__":
    main()
