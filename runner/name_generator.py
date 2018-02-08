'''
Created on Jan 10, 2014

@author: robb
'''

import argparse
import logging
import random
import os

log = logging.getLogger('runner')


def load(reload_files=False,
         fnoun=os.path.join(os.getcwd(), '../sql/nouns.txt'),
         fadj=os.path.join(os.getcwd(), '../sql/adjectives.txt')):

    nouns = []
    adjectives = []
    if reload_files or nouns is None or 0 == len(nouns):
        with open(fnoun) as f:
            nouns = f.read().splitlines()
            log.info('Loaded {} nouns from {}'.format(len(nouns), fnoun))

        with open(fadj) as f:
            adjectives = f.read().splitlines()
            log.info('Loaded {} adjectives from {}'.format(len(adjectives), fadj))

    return nouns, adjectives


def make_names(nouns, adjectives, pair_count: int=3):
    ''' Returns a list of tuple pairs for use in Django's admin 'choices' drop-list. '''
    result = []
    n = random.choices(nouns, k=pair_count)
    a = random.choices(adjectives, k=pair_count)
    for x in range(pair_count):
        if random.choice([True, False]):
            name1 = name_format2(n[x], a[x])
            result.append((name1, name1))
        else:
            name2 = name1 = name_format1(n[x], a[x])
            result.append((name2, name2))
    return result


def name_format1(n, a):
    return 'The ' + a + ' ' + n


def name_format2(n, a):
    return n + ' the ' + a


def get_random_name():
    names = make_names(1)
    return random.sample(list(names), 1)


def format_sql_insert(name):
    return f'insert into runner_racername(name) values ("{name}");\n'


def format_text(name):
    return f'{name}'


def emit_names(names, fmt):
    outputf = format_sql_insert if fmt == 'sql' else format_text
    for name in names:
        print(outputf(name))


def main(n: int=3, fmt='text'):
    nouns, adjectives = load()
    names = make_names(nouns, adjectives, n)
    emit_names(names, fmt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('n', type=int, help='Number of names to generate')
    parser.add_argument('output', choices=['text', 'sql'])
    args = parser.parse_args()
    main(args.n, args.output)
