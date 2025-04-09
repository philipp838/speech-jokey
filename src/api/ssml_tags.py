"""ssml_wrapper.py

"""

ssml_tags = {
    "⏸️": ('<break time="2s"/>', ""),
    "😐": ("<emphasis level=\"reduced\">", "</emphasis>"),
    "🙂": ("<emphasis level=\"moderate\">", "</emphasis>"),
    "😁": ("<emphasis level=\"strong\">", "</emphasis>"),
    "🔈": ("<prosody volume=\"silent\">", "</prosody>"),
    "🔉": ("<prosody volume=\"medium\">", "</prosody>"),
    "🔊": ("<prosody volume=\"loud\">", "</prosody>"),
    "🐌": ("<prosody rate=\"slow\">", "</prosody>"),
    "🚶": ("<prosody rate=\"medium\">", "</prosody>"),
    "🏃": ("<prosody rate=\"fast\">", "</prosody>"),
    "🗣️⬇️": ("<prosody pitch=\"low\">", "</prosody>"),
    "🗣️⬆️": ("<prosody pitch=\"high\">", "</prosody>"),
    "🗣️⏫": ("<prosody pitch=\"x-high\">", "</prosody>"),
    "🌏": ("<lang xml:lang=\"en-US\">", "</lang>")
}
