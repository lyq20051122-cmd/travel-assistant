BLOCK_WORDS = [
    "爆炸",
    "恐袭",
    "偷渡"
]

def safety_check(message):

    for word in BLOCK_WORDS:

        if word in message:
            return "BLOCK"

    return "PASS"