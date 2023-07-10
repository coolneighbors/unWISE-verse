
def generate_legacy_survey_url(RA, DEC, zoom = 14):
    legacy_survey_template_url = "https://www.legacysurvey.org/viewer?ra={}&dec={}&layer=unwise-neo6&zoom={}&mark={},{}"
    return legacy_survey_template_url.format(RA,DEC,zoom,RA,DEC)

def generate_SIMBAD_url(RA, DEC, radius = 60):
    SIMBAD_template_url = "http://simbad.u-strasbg.fr/simbad/sim-coo?Coord={}+{}&Radius={}&Radius.unit=arcsec"
    return SIMBAD_template_url.format(RA,DEC,radius)

def generate_VizieR_url(RA, DEC,FOV):
    VizieR_template_url = "https://vizier.u-strasbg.fr/viz-bin/VizieR?-c={}+{}&-c.bs={}x{}&-out.add=_r&-out.add=_RAJ%2C_DEJ&-sort=_r&-to=&-out.max=20&-meta.ucd=2&-meta.foot=1&-oc.form=d"
    return VizieR_template_url.format(RA, DEC, FOV, FOV)

def generate_IRSA_url(RA, DEC):
    IRSA_template_url = "https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api?mode=getResult&subsetsize=11.7333&locstr={}+{}&survey=DSS%2CSDSS%2C2MASS%2CSEIP%2CWISE"
    return IRSA_template_url.format(RA,DEC)
