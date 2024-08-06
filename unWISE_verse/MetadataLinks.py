
def generate_legacy_survey_url(RA, DEC, zoom = 14):
    """
    Generates a URL for the Legacy Survey Viewer

    Parameters
    ----------
    RA : float
        Right Ascension of the object in degrees in ICRS frame, J2000 equinox.
    DEC : float
        Declination of the object in degrees in ICRS frame, J2000 equinox.
    zoom : int
        Zoom level of the viewer. Default is 14.

    Returns
    -------
    legacy_survey_template_url : str
        URL for the Legacy Survey Viewer with the given RA, DEC and zoom level.
    """

    legacy_survey_template_url = "https://www.legacysurvey.org/viewer?ra={}&dec={}&layer=unwise-neo6&zoom={}&mark={},{}"
    return legacy_survey_template_url.format(RA,DEC,zoom,RA,DEC)

def generate_SIMBAD_url(RA, DEC, radius=60):
    """
    Generates a URL for the SIMBAD database

    Parameters
    ----------
    RA : float
        Right Ascension of the object in degrees in ICRS frame, J2000 equinox.
    DEC : float
        Declination of the object in degrees in ICRS frame, J2000 equinox.
    radius : float
        Radius of the search in arcseconds. Default is 60 arcseconds.

    Returns
    -------
    SIMBAD_template_url : str
        URL for the SIMBAD database with the given RA, DEC and radius.
    """

    SIMBAD_template_url = "http://simbad.u-strasbg.fr/simbad/sim-coo?Coord={}+{}&Radius={}&Radius.unit=arcsec"
    return SIMBAD_template_url.format(RA,DEC,radius)

def generate_VizieR_url(RA, DEC, FOV):
    """
    Generates a URL for the VizieR database

    Parameters
    ----------
    RA : float
        Right Ascension of the object in degrees in ICRS frame, J2000 equinox.
    DEC : float
        Declination of the object in degrees in ICRS frame, J2000 equinox.
    FOV : float
        Field of View of the search in arcseconds.

    Returns
    -------
    VizieR_template_url : str
        URL for the VizieR database with the given RA, DEC and FOV.
    """

    VizieR_template_url = "https://vizier.u-strasbg.fr/viz-bin/VizieR?-c={}+{}&-c.bs={}x{}&-out.add=_r&-out.add=_RAJ%2C_DEJ&-sort=_r&-to=&-out.max=20&-meta.ucd=2&-meta.foot=1&-oc.form=d"
    return VizieR_template_url.format(RA, DEC, FOV, FOV)

def generate_IRSA_url(RA, DEC):
    """
    Generates a URL for the IRSA database
    Parameters
    ----------
    RA : float
        Right Ascension of the object in degrees in ICRS frame, J2000 equinox.
    DEC : float
        Declination of the object in degrees in ICRS frame, J2000 equinox.

    Returns
    -------
    IRSA_template_url : str
        URL for the IRSA database with the given RA, DEC.
    """

    IRSA_template_url = "https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api?mode=getResult&subsetsize=11.7333&locstr={}+{}&survey=DSS%2CSDSS%2C2MASS%2CSEIP%2CWISE"
    return IRSA_template_url.format(RA,DEC)
