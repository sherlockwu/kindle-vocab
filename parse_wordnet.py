#!/usr/bin/python
import os, json

def main():
    root = 'wordnet'
    words = {}
    for path in os.listdir(root):
        path = os.path.join(root, path)
        with open(path) as f:
            for l in f:
                parts = l.split('|')
                if len(parts) != 2:
                    continue
                definition = parts[1].strip()
                word = parts[0].split()[4]
                word = word.lower().replace('_', ' ')
                words[word] = definition
    print json.dumps(words, indent=2, sort_keys=True)
if __name__ == '__main__':
    main()
