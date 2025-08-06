import argparse
import ciclone
from ciclone import *

import click
import json


@click.command()
@click.argument('filename')
def main(filename):
    try:
        f = open(filename, 'r')
    except FileNotFoundError:
        raise click.FileError(filename)
    read = f.readline()
    _json = json.loads(read)

    click.echo("CICLONE2")
    click.echo(f'{filename} model opened with {len(_json)} elements:')

    model = ciclone.Model()
    model.debug = True
    _until = ''
    comm = dict()
    for key, val in _json.items():
        key = int(key)
        match = {'que': 'Queue', 'com': 'Combi', 'nor': 'Normal', 'cou': 'Count', 'func': 'Func'}
        elem = match[val['id'].split('_')[-1]]
        if elem == 'Combi':
            comm[key] = eval(f'ciclone.{elem}("{val["desc"]}", {val["pre"]}, {val["fol"]}, {val["duration"]})')
        elif elem == 'Normal':
            comm[key] = eval(f'ciclone.{elem}("{val["desc"]}", {val["fol"]}, {val["duration"]})')
        elif elem == 'Queue':
            comm[key] = eval(f'ciclone.{elem}("{val["desc"]}", {val["length"]}, {val["start"]})')
        elif elem == 'Count':
            comm[key] = eval(f'ciclone.{elem}("{val["desc"]}", {val["fol"]})')
            _until = f'model.until(Count{key}={val["until"]})'
        elif elem == 'Func':
            comm[key] = eval(f'ciclone.{elem}("{val["desc"]}", {val["fol"]}, {val["con"]})')
    model.add(comm)
    exec(_until)

    # print(model.env.command.all)
    for x in model.env.command.values():
        print(x)

    model.run()

    # print('#111')
    # for x in model.env.data:
    #     print(x)

    print(f'\nElapsed time: {model.time/4*1000:.3f} ms')
    click.echo(f'Saved the result to {filename} of "out" item')
    click.echo('Done.')


if __name__ == "__main__":
    main()
