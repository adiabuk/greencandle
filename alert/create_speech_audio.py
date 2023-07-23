"""
Create mp3 with systhesized text
"""

import sys
from alertlibs import create_polly_voice, create_google_voice

def main():
    """
    Create mp3 with synthesized voice from Amazon and Google
    """
    engines = ['polly', 'google']
    if len(sys.argv) > 1 and sys.argv[1] in engines:
        engine = sys.argv[1]
    else:
        print(f"Usage: {sys.argv[0]} <polly|google>")
        sys.exit(1)

    with open('text.txt', 'r') as text_file:
        text = text_file.read()

    if engine == 'polly':
        create_polly_voice(text, '/srv/output/polly_output.mp3')
    if engine == 'google':
        create_google_voice(text, '/srv/output/google_output.mp3')
if __name__ == '__main__':
    main()
