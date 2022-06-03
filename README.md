```
python one_wiseview_gif.py --help
usage: one_wiseview_gif.py [-h] [--outdir OUTDIR] [--minbright MINBRIGHT] [--maxbright MAXBRIGHT] [--duration DURATION] [--keep_pngs] ra dec gifname

generate one WiseView style unWISE image blink

positional arguments:
  ra                    RA in decimal degrees.
  dec                   Dec in decimal degrees.
  gifname               Name of output GIF animation file.

optional arguments:
  -h, --help            show this help message and exit
  --outdir OUTDIR       Output directory for PNGs.
  --minbright MINBRIGHT
                        Image rendering stretch lower bound.
  --maxbright MAXBRIGHT
                        image rendering stretch upper bound.
  --duration DURATION   Time in seconds per frame.
  --keep_pngs           Retain the PNGs after the GIF has been built?
```

Optional Usage:

Reading from CSV - 
In manifest.csv, put RA and DEC of objects in the RA and DEC columns 
