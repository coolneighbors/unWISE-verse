from wv import one_wv_animation

def wise0855():
    
  ra = 133.786245
  dec = -7.244372

  outdir = 'w0855'
  gifname = 'w0855.gif'
  one_wv_animation(ra, dec, outdir, gifname)

def w1930():

  # byw example at ~1.5 asec/yr
  ra = 292.725665
  dec = -20.998843

  outdir = 'w1930'
  gifname = 'w1930.gif'

  one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)

def w2243():

  # byw example at ~0.5+ asec/yr
  ra = 340.8321592 
  dec = -14.9839027

  outdir = 'w2243'
  gifname = 'w2243.gif'

  one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)

def w1553():

    # byw example showing blending

    ra = 238.44587574
    dec = 69.56790675

    outdir = 'w1553'
    gifname = 'w1553.gif'

    one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)

def j0002():

    # melina's wd companion in the galactic plane

    ra = 0.6225026
    dec = 63.8712344

    outdir = 'w0002'
    gifname = 'w0002.gif'

    one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)

def j1936():
    # maybe a better crowded field example...

    ra = 294.233532
    dec = 4.134037

    outdir = 'w1936'
    gifname = 'w1936.gif'

    one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)

def _ghost():
    

    ra = 12.4397
    dec = -13.5258

    outdir = 'ghost'
    gifname = 'ghost.gif'

    one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)

def _diff_spike():

    ra = 34.2739
    dec = -4.1872

    outdir = 'diff_spike'
    gifname = 'diffraction_spike.gif'

    one_wv_animation(ra, dec, outdir, gifname, minbright=-12.5, maxbright=125)
