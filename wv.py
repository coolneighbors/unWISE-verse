import requests
import os
import shutil
from PIL import Image

png_anim = "https://vjxontvb73.execute-api.us-west-2.amazonaws.com/png-animation"
amnh_base_url = "https://amnh-citsci-public.s3-us-west-2.amazonaws.com/"

def default_params():
    """
    Get a dummy dictionary of WiseView API parameters.

    Returns
    -------
        params : dict
            Dummy dictionary of WiseView API parameters.

    Notes
    -----
        Default (RA, Dec) are those of WISE 0855.
        We should figure out what the units of "size" are.

    """

    params = {
        "ra": 133.786245,
        "dec": -7.244372,
        "band": 3,
        "size": 128,
        "max_dyr": 0,
        "minbright": -50.0000,
        "maxbright": 500.0000,
        "invert": 1,
        "stretch": 1,
        "diff": 0,
        "scandir": 0,
        "outer": 0,
        "neowise": 0,
        "window": 0.5,
        "diff_window": 1,
        "unique": 1,
        "smooth_scan": 0,
        "shift": 0,
        "pmx": 0,
        "pmy": 0,
        "synth_a": 0,
        "synth_a_sub": 0,
        "synth_a_ra": "",
        "synth_a_dec": "",
        "synth_a_w1": "",
        "synth_a_w2": "",
        "synth_a_pmra": 0,
        "synth_a_pmdec": 0,
        "synth_a_mjd": "",
        "synth_b": 0,
        "synth_b_sub": 0,
        "synth_b_ra": "",
        "synth_b_dec": "",
        "synth_b_w1": "",
        "synth_b_w2": "",
        "synth_b_pmra": 0,
        "synth_b_pmdec": 0,
        "synth_b_mjd": "",
    }

    return params

def custom_params(ra, dec, minbright=None, maxbright=None):
    """
    Dictionary of WiseView API query parameters.

    Parameters
    ----------
        ra : float
            RA in decimal degrees.
        dec : float
            Dec in decimal degrees.
        minbright : float, optional
            WiseView image stretch lower pixel value. Default of None
            picks up default value from default_params() utility.
        maxbright : float, optional
            WiseView image stretch upper pixel value. Default of None
            picks up default value from default_params() utility.

    Returns
    -------
        params : dict
            WiseView API query parameters for requested sky location and image
            stretch.

    Notes
    -----
        Would be good to generalize so that more parameters can be customized
        beyond just the central (RA, Dec) and the image stretch upper/lower
        bounds.

    """

    params = default_params()
    params['ra'] = ra
    params['dec'] = dec
    if minbright is not None:
        params['minbright'] = minbright
    if maxbright is not None:
        params['maxbright'] = maxbright

    return params

def get_radec_urls(ra, dec, minbright=None, maxbright=None):
    """
    Get a list of WiseView image URLs for a desired blink.

    Parameters
    ----------
        ra : float
            RA in decimal degrees.
        dec : float
            Dec in decimal degrees.
        minbright : float, optional
            WiseView image stretch lower pixel value. Default of None
            picks up default value from default_params() utility.
        maxbright : float, optional
            WiseView image stretch upper pixel value. Default of None
            picks up default value from default_params() utility.

    Returns
    -------
        urls : list
            List of string URLs gathered from the WiseView API.

    """

    params = custom_params(ra, dec, minbright=minbright, maxbright=maxbright)

    res = requests.get(png_anim,params=params)

    # what is going on with these printouts? do we need them?
    # can they be made better?
    #print("JSON Response:")
    #print(res.json())
    #print("PNG Links:")
    urls = []
    for lnk in res.json()["ims"]:
        url = amnh_base_url + lnk
        urls.append(url)

    return urls

def _download_one_png(url, outdir, fieldName):
    """
    Download one PNG image based on its URL.

    Parameters
    ----------
        url : str
            Download URL.
        outdir : str
            Output directory.

    Returns
    -------
        fname_dest : str
            Destination file name to which the PNG was downloaded.

    Notes
    -----
        'url' here should be just a string, not an array or list of strings.

    """

    fname = os.path.basename(fieldName)
    fname_dest = os.path.join(outdir, fname)

    r = requests.get(url)

    open(fname_dest, 'wb').write(r.content)

    return fname_dest

def gif_from_pngs(flist, gifname, duration=0.2, scale_factor=1.0):
    """
    Construct a GIF animation from a list of PNG files.

    Parameters
    ----------
        flist : list
            List of (full path) file names of PNG images from which to
            construct the GIF animatino.
        gifname : str
            Output file name (full path) for the GIF animation.
        duration : float
            Time interval in seconds for each frame in the GIF blink (?).
        scale_factor : float
            PNG image size scaling factor

    Notes
    -----
         Order in which the PNGs appear in the GIF is dictated by the
         order of the file names in 'flist'.

    """

    import imageio

    # add checks on whether the files in flist actually exist?

    # Rescales PNGs
    if(scale_factor != 1.0):
        for f in flist:
            im = Image.open(f)
            size = im.size
            width = size[0]
            height = size[1]
            rescaled_size = (width * scale_factor,height * scale_factor)
            resize_png(f,rescaled_size)


    images = []
    for f in flist:
        images.append(imageio.imread(f))

    imageio.mimsave(gifname, images, duration=duration)

def png_set(ra, dec, outdir, minbright=None, maxbright=None,scale_factor=1.0):
    counter = 0
    assert(os.path.exists(outdir))

    urls = get_radec_urls(ra, dec, minbright=minbright, maxbright=maxbright)

    flist = []
    
    for url in urls:
        counter+=1
        fieldName='field-RA'+str(ra)+'-DEC'+str(dec)+'-'+str(counter)+'.png'
        fname_dest = _download_one_png(url, outdir, fieldName)
        flist.append(fname_dest)
    
    #make sure 10 images are saved for each png - if less than 10, copy last frame until there are ten
    savedURL=url
    while len(flist) < 10:
        counter+=1
        
        newFieldName='field-RA'+str(ra)+'-DEC'+str(dec)+'-'+str(counter)+'.png'
        fname_dest = _download_one_png(savedURL, outdir, newFieldName)
        flist.append(fname_dest)

    # Rescales PNGs
    if (scale_factor != 1.0):
        for f in flist:
            im = Image.open(f)
            size = im.size
            width = size[0]
            height = size[1]
            rescaled_size = (width * scale_factor, height * scale_factor)
            resize_png(f, rescaled_size)

    return flist


def resize_png(filename,size):
    """
       Overwrite PNG file with a particular width and height

       Parameters
       ----------
           filename : string
               Full path filename with filetype of the desired PNG file.
           size : tuple, (int,int)
               Width and height of the new PNG

       Notes
       -----
        Should PNG files be overridden or should they just be created in addition to the original PNG?

        Resampling parameter for resizing function is something that should be considered more.
        The current one, LANCZOS, is native to PILLOW and in their documentation it says it is the
        one which the best upscaling/downscaling quality

        Could possibly implement a keep_aspect_ratio parameter, but our images should all be squares.
    """

    im = Image.open(filename)
    resized_image = im.resize(size,Image.Resampling.LANCZOS)
    #new_filename = filename.replace(".png","") + "_resized" + ".png"
    resized_image.save(filename)
    return filename

def one_wv_animation(ra, dec, outdir, gifname, minbright=None,
                     maxbright=None, duration=0.2, delete_pngs=True):
    
    #Counter, used to determine png chronology
    counter = 0
    """
    Create one WiseView animation at a desired central sky location.

    Parameters
    ----------
        ra : float
            RA in decimal degrees.
        dec : float
            Dec in decimal degrees.
        outdir : str
            Output directory **of the PNGs**.
        gifname : str
            Output file name (full path) for the GIF animation.
        minbright : float, optional
            WiseView image stretch lower pixel value. Default of None
            picks up default value from default_params() utility.
        maxbright : float, optional
            WiseView image stretch upper pixel value. Default of None
            picks up default value from default_params() utility.
        duration : float, optional
            Time interval in seconds for each frame in the GIF blink (?).
        delete_pngs : bool, optional
            Delete downloaded PNGs after having used them to construct the GIF?

    Notes
    -----
        Should we make the output directory in the event that it doesn't
        already exist?
        'gifname' and 'outdir' arguments could potentially be combined
        into one argument that gives the full desired output file path.
        Currently, the GIF gets written into the current working directory. It
        would be better to make the GIF output directory configurable.
        Would be nice to add some more 'logging' type of printouts.

    """

    assert(os.path.exists(outdir))

    urls = get_radec_urls(ra, dec, minbright=None, maxbright=None)

    flist = []
    
    for url in urls:
        fieldName='field-RA'+str(ra)+'-DEC'+str(dec)+'-'+str(counter)+'.png'
        fname_dest = _download_one_png(url, outdir, fieldName)
        flist.append(fname_dest)
        counter+=1

    gif_from_pngs(flist, gifname, duration=duration)

    if delete_pngs:
        print('Cleaning up...')
        for f in flist:
            os.remove(f)
