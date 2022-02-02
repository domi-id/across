# Action SuperCross Python Library

Python library to parse resource files, level files, and replay files for
[Action SuperCross](https://elastomania.com) videogame.
The library supports all versions of the game.

## Prerequisites

* [Python](https://python.org) 3.6 or newer;
* [Construct](https://construct.readthedocs.io) 2.8.7 — 2.8.22: `pip3 install -r requirements.txt`.
  Other versions of construct will not work.

## Usage

### Resource files

For every file stored in a .res file print its name and size: 

```python
from across.res import ResourceFile

with open(path, "rb") as f:
    res = ResourceFile.parse(f.read())

for fname, data in res.items():
    print(fname, len(data))
```

Unpack `across.res` file into `unpacked` folder:
```python
from across.res import unpack_res

unpack_res("across.res", "unpacked")
```

### Level files

Print title of a level, number of polygons and objects in a level,
then coordinates of start and finish: 

```python
from across.level import Level

with open(path, "rb") as f:
    lev = Level.parse(f.read())

print(f"{lev.title} has {len(lev.polygons)} polygons and {len(lev.objects)} objects")
for o in lev.objects:
    if o.type == "start":
        print("Start position", o.x, o.y)
    if o.type == "flower":
        print("Finish position", o.x, o.y)
```

### Replay files

Print internal on which the replay was made, replay duration, position of the bike at the beginning,
position of the right wheel at the end: 

```python
from across.replay import Replay

with open(path, "rb") as f:
    rec = Replay.parse(f.read())

print(f"Replay for internal #{rec.internal_num}: {rec.frames_num / 60}s")
print(f"Bike at start: {(rec.frames[0].bike_x, rec.frames[0].bike_y)}")
print(f"Right wheel at finish: {(rec.frames[-1].rwhl_x, rec.frames[-1].rwhl_y)}")
```

## Known bugs and limitations

The code has only been tested for correct parsing on a limited number of files. 
Building of files might or might not be broken.
