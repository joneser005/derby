'''
Created on Jan 10, 2014

@author: robb
'''
import logging
import random

import os

log = logging.getLogger('runner')

nouns = []
adjectives = []


def load(reload_files=False,
         fnoun=os.path.join(CURRENT_PATH, '../sql/nouns.txt'),
         fadj=os.path.join(CURRENT_PATH, '../sql/adjectives.txt')):
    global nouns
    global adjectives

    if reload_files or nouns is None or 0 == len(nouns):
        with open(fnoun) as f:
            nouns = f.read().splitlines()
            log.info('Loaded {} nouns from {}'.format(len(nouns), fnoun))

        with open(fadj) as f:
            adjectives = f.read().splitlines()
            log.info('Loaded {} adjectives from {}'.format(len(adjectives), fadj))


def make_names(pair_count=3):
    ''' Returns a list of tuple pairs for use in Django's admin 'choices' drop-list. '''
    n = random.sample(nouns, pair_count)
    a = random.sample(adjectives, pair_count)
    result = []
    for x in range(pair_count):
        name1 = getFormat1(n[x], a[x])
        result.append((name1, name1))
        name2 = name1 = getFormat2(n[x], a[x])
        result.append((name2, name2))
    return result


def getFormat1(n, a):
    return 'The ' + a + ' ' + n


def getFormat2(n, a):
    return n + ' the ' + a


def getRandomName():
    names = make_names(1)
    return random.sample(list(names), 1)


def getInsert(name):
    return 'insert into runner_racername(name) values ("{}");\n'.format(name)


def main():
    print('Loading values...')
    load()
    #     print('Generating 100 name pairs...')
    #     for x in range(100):
    #         print make_names()
    print('Generating sql inserts...')
    with open(os.path.join(CURRENT_PATH, '../sql/name_inserts.sql'), 'w') as f:
        for n in nouns:
            for a in adjectives:
                f.write(getInsert(getFormat1(n, a)))
                f.write(getInsert(getFormat2(n, a)))


if __name__ == '__main__':
    main()
