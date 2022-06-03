import requests

png_anim = "https://vjxontvb73.execute-api.us-west-2.amazonaws.com/png-animation"
params = {
    "ra": 133.786245,
    "dec": -7.244372,
    "band": 3,
    "size": 64,
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
res = requests.get(png_anim,params=params)
print("JSON Response:")
print(res.json())
print("PNG Links:")
for lnk in res.json()["ims"]:
    print("https://amnh-citsci-public.s3-us-west-2.amazonaws.com/"+lnk)

